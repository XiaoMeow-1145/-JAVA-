# ==============================
# Extension Function Menu (Visual File/Folder Selection + Custom Main Menu + Fixed Window Size)
# ==============================

# Set UTF-8 to avoid crash/garbled characters
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 > $null

# Fix PowerShell window size to 1024x1024 pixels
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinAPI {
    [DllImport("kernel32.dll", ExactSpelling=true)]
    public static extern IntPtr GetConsoleWindow();
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool MoveWindow(IntPtr hWnd, int X, int Y, int nWidth, int nHeight, bool bRepaint);
}
"@

$hwnd = [WinAPI]::GetConsoleWindow()
[WinAPI]::MoveWindow($hwnd, 100, 100, 1024, 1024, $true)

# Load Windows Forms for file/folder dialogs
Add-Type -AssemblyName System.Windows.Forms

# Default mod folder path
$global:ModFolder = "D:\Minecraft\mods"

function Show-Menu {
    Clear-Host
    Write-Host "==========================" -ForegroundColor Cyan
    Write-Host "     Extension Menu" -ForegroundColor Yellow
    Write-Host "==========================" -ForegroundColor Cyan
    Write-Host "1. Import Mod"
    Write-Host "2. Set Mod Folder Path"
    Write-Host "3. Import Shader Pack (zip)"
    Write-Host "4. Import Resource Pack"
    Write-Host "5. Return to Main Menu (select .ps1 file)"
    Write-Host "0. Exit"
}

# Generic file selection function
function Select-File($filter, $title) {
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Filter = $filter
    $dialog.Title = $title
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        return $dialog.FileName
    } else {
        return $null
    }
}

# Generic folder selection function
function Select-Folder($description) {
    $folderDialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderDialog.Description = $description
    $folderDialog.ShowNewFolderButton = $true
    if ($folderDialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        return $folderDialog.SelectedPath
    } else {
        return $null
    }
}

# 1. Import Mod
function Import-Mod {
    $file = Select-File "Minecraft Mods (*.jar)|*.jar" "Select a Mod file"
    if ($file -and (Test-Path $file)) {
        Copy-Item $file -Destination $global:ModFolder -Force
        Write-Host "Mod imported successfully: $file" -ForegroundColor Green
    } else {
        Write-Host "No file selected or file not found." -ForegroundColor Red
    }
    Pause
}

# 2. Set Mod Folder Path
function Set-ModFolder {
    $folder = Select-Folder "Select the Mod Folder"
    if ($folder) {
        $global:ModFolder = $folder
        Write-Host "Mod folder path updated to: $global:ModFolder" -ForegroundColor Green
    } else {
        Write-Host "No folder selected." -ForegroundColor Red
    }
    Pause
}

# 3. Import Shader Pack
function Import-Shader {
    $file = Select-File "Shader Packs (*.zip)|*.zip" "Select a Shader Pack"
    $shaderFolder = "D:\Minecraft\shaderpacks"
    if (-not (Test-Path $shaderFolder)) {
        New-Item -ItemType Directory -Path $shaderFolder -Force | Out-Null
    }
    if ($file -and (Test-Path $file)) {
        Copy-Item $file -Destination $shaderFolder -Force
        Write-Host "Shader pack imported successfully: $file" -ForegroundColor Green
    } else {
        Write-Host "No file selected or file not found." -ForegroundColor Red
    }
    Pause
}

# 4. Import Resource Pack
function Import-ResourcePack {
    $file = Select-File "Resource Packs (*.zip)|*.zip" "Select a Resource Pack"
    $resourceFolder = "D:\Minecraft\resourcepacks"
    if (-not (Test-Path $resourceFolder)) {
        New-Item -ItemType Directory -Path $resourceFolder -Force | Out-Null
    }
    if ($file -and (Test-Path $file)) {
        Copy-Item $file -Destination $resourceFolder -Force
        Write-Host "Resource pack imported successfully: $file" -ForegroundColor Green
    } else {
        Write-Host "No file selected or file not found." -ForegroundColor Red
    }
    Pause
}

# 5. Return to Main Menu (select .ps1 file)
function Return-MainMenu {
    $file = Select-File "PowerShell Scripts (*.ps1)|*.ps1" "Select the Main Menu Script"
    if ($file -and (Test-Path $file)) {
        Write-Host "Launching main menu script: $file" -ForegroundColor Green
        Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy Bypass", "-File `"$file`""
        exit
    } else {
        Write-Host "No file selected or file not found." -ForegroundColor Red
        Pause
    }
}

# Main loop
do {
    Show-Menu
    $choice = Read-Host "Choose an option"

    switch ($choice) {
        "1" { Import-Mod }
        "2" { Set-ModFolder }
        "3" { Import-Shader }
        "4" { Import-ResourcePack }
        "5" { Return-MainMenu }
        "0" { break }
        default { Write-Host "Invalid option, please try again." -ForegroundColor Red; Pause }
    }
} while ($choice -ne "0")