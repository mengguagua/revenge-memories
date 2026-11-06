// Read-only browser QA helper. Uses the actual rendered boxes, never clips text.
// Run in a browser page / browser automation after each language or viewport change.
export function auditWebsiteLayout(){
  const failures=[];
  for(const e of document.querySelectorAll('button,.button,summary,.header-cta,.facts>div')){
    const r=e.getBoundingClientRect();
    if(!r.width||!r.height||e.closest('dialog:not([open])')||e.closest('[hidden]'))continue;
    for(const n of e.querySelectorAll('span,strong,small,p')){
      if(n.children.length||!n.textContent.trim())continue;
      const q=n.getBoundingClientRect();
      if(!q.width||!q.height)continue;
      if(q.left<r.left+2||q.right>r.right-2||q.top<r.top+2||q.bottom>r.bottom-2)
        failures.push({text:n.textContent.trim(),control:e.className,gaps:[q.left-r.left,r.right-q.right,q.top-r.top,r.bottom-q.bottom]});
    }
  }
  return {language:document.documentElement.lang,width:innerWidth,height:innerHeight,horizontal_overflow:document.documentElement.scrollWidth>innerWidth,text_safety_failures:failures};
}
