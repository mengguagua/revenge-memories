#!/usr/bin/env python3
"""Reuse the established single-idle integration for the jaw/neck revision."""
import integrate_brigand_idle_v2 as integration
integration.OUT=integration.ROOT/'brigand-idle-jaw-v3-20261023'
if __name__=='__main__': integration.main()
