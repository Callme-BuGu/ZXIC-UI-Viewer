# 弹出文件夹选择框，让用户选择从设备提取的 web 文件夹
# 用法：由"选择web文件夹.bat"调用，把选中的路径输出到 stdout
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = "请选择从设备提取的 web 文件夹（内含 index.html、css、js、subpg 等）"
$dialog.ShowNewFolderButton = $false
$dialog.SelectedPath = $PSScriptRoot

if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
    # 只输出路径，供 bat 捕获
    Write-Output $dialog.SelectedPath
}