Option Explicit

Dim fso, shell, scriptDir, mainFile, pythonwPath, command, dryRun
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
mainFile = fso.BuildPath(scriptDir, "main.py")
pythonwPath = fso.BuildPath(scriptDir, ".venv\Scripts\pythonw.exe")
dryRun = False

If WScript.Arguments.Count > 0 Then
    If LCase(WScript.Arguments(0)) = "--dry-run" Then
        dryRun = True
    End If
End If

If Not fso.FileExists(mainFile) Then
    MsgBox "main.py not found in: " & scriptDir, vbCritical, "Mini SC Timer"
    WScript.Quit 1
End If

If Not fso.FileExists(pythonwPath) Then
    MsgBox "Virtual environment not found. Run setup.cmd first.", vbExclamation, "Mini SC Timer"
    WScript.Quit 1
End If

shell.CurrentDirectory = scriptDir
command = Chr(34) & pythonwPath & Chr(34) & " " & Chr(34) & mainFile & Chr(34)

If dryRun Then
    WScript.Echo command
    WScript.Quit 0
End If

shell.Run command, 0, False
