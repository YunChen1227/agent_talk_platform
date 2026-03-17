# START

powershell -Command "Start-Process powershell -ArgumentList '-NoExit','-ExecutionPolicy Bypass','-File','C:\workspace\agent_talk_platform\start-services.ps1' -Verb RunAs"

# STOP

powershell -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass','-File','C:\workspace\agent_talk_platform\stop-services.ps1' -Verb RunAs"