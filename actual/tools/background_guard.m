// Test-process-only guard. Loaded before Godot's main(): no native window may
// be ordered onto the desktop and no application activation request may run.
// This does not inspect or manipulate any other app/window and never ships.
#import <Cocoa/Cocoa.h>
#import <objc/runtime.h>
#include <stdlib.h>
static void ignore0(id self, SEL selector) {}
static void ignoreObject(id self, SEL selector, id value) {}
static void ignoreBool(id self, SEL selector, BOOL value) {}
static void ignoreOrder(id self, SEL selector, NSWindowOrderingMode mode, NSInteger relative) {}
static BOOL denyActivation(id self, SEL selector, NSApplicationActivationOptions options) { return NO; }
static BOOL denyPolicy(id self, SEL selector, NSApplicationActivationPolicy policy) { return NO; }
static void replace(Class cls, const char *name, IMP imp) {
    SEL selector=sel_registerName(name);
    Method method=class_getInstanceMethod(cls,selector);
    if (!method) return;
    class_replaceMethod(cls,selector,imp,method_getTypeEncoding(method));
}
__attribute__((constructor)) static void guard_start(void) {
    @autoreleasepool {
        // Suppress both the initial activation and the engine's delayed workaround.
        replace(NSClassFromString(@"GodotApplication"),"activateApplication",(IMP)ignore0);
        replace(NSClassFromString(@"GodotApplication"),"forceUnbundledWindowActivationHackStep1",(IMP)ignore0);
        replace([NSApplication class],"activateIgnoringOtherApps:",(IMP)ignoreBool);
        replace([NSApplication class],"activate",(IMP)ignore0);
        replace([NSApplication class],"setActivationPolicy:",(IMP)denyPolicy);
        replace([NSRunningApplication class],"activateWithOptions:",(IMP)denyActivation);
        int count=objc_getClassList(NULL,0);
        Class *classes=calloc(count,sizeof(Class));
        count=objc_getClassList(classes,count);
        for (int i=0;i<count;i++) {
            Class cls=classes[i], parent=cls;
            while (parent && parent!=[NSWindow class]) parent=class_getSuperclass(parent);
            if (!parent) continue;
            replace(cls,"orderWindow:relativeTo:",(IMP)ignoreOrder);
            replace(cls,"orderFront:",(IMP)ignoreObject);
            replace(cls,"orderFrontRegardless",(IMP)ignore0);
            replace(cls,"makeKeyAndOrderFront:",(IMP)ignoreObject);
            replace(cls,"makeKeyWindow",(IMP)ignore0);
            replace(cls,"setIsVisible:",(IMP)ignoreBool);
            replace(cls,"miniaturize:",(IMP)ignoreObject);
            replace(cls,"deminiaturize:",(IMP)ignoreObject);
        }
        free(classes);
        setenv("CHRONO_BACKGROUND_GUARD_ACTIVE","1",1);
    }
}
