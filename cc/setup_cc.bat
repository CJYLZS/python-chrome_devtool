@echo off
setlocal EnableDelayedExpansion
reg add HKEY_CURRENT_USER\Software\Google\Chrome\NativeMessagingHosts\chrome_commucation /t REG_SZ /d %~dp0cc_config.json /f
python setup_cc.py