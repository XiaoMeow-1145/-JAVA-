# Set terminal title
$Host.UI.RawUI.WindowTitle = "Netease MC Tool"

function Show-Menu {
    Clear-Host
    # ASCII art title for "Netease MC Tool"
    Write-Host " _   _      _                    _             __  __ ____               _       " -ForegroundColor Cyan
    Write-Host "| \ | | ___| |_ __ _ _ __   __ _| | _____     |  \/  / ___|_ __ ___  ___ | | __   " -ForegroundColor Cyan
    Write-Host "|  \| |/ _ \ __/ _` | '_ \ / _` | |/ / _ \    | |\/| | |   | '__/ _ \/ _ \| |/ /   " -ForegroundColor Cyan
    Write-Host "| |\  |  __/ || (_| | | | | (_| |   <  __/    | |  | | |___| | |  __/ (_) |   <    " -ForegroundColor Cyan
    Write-Host "|_| \_|\___|\__\__,_|_| |_|\__/|_|\_\___|    |_|  |_|\____|_|  \___|\___/|_|\_\   " -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Start detection tool (delete target jar, restore deleted jars, backup and restore config)" -ForegroundColor Green
    Write-Host "2. Backup all mods (.jar files) (once only)" -ForegroundColor Green
    Write-Host "3. Open mods folder (D:\MCLDownload\Game\.minecraft\mods)" -ForegroundColor Green
    Write-Host "4. Open .minecraft folder (D:\MCLDownload\Game\.minecraft)" -ForegroundColor Green
    Write-Host "5. Create shaderpacks folder" -ForegroundColor Green
    Write-Host "6. Open shaderpacks folder (D:\MCLDownload\Game\.minecraft\shaderpacks)" -ForegroundColor Green
    Write-Host "7. Delete all mods (.jar files) in mods folder" -ForegroundColor Red
    Write-Host "8. Restore mods from backup" -ForegroundColor Green
    Write-Host "0. Exit" -ForegroundColor Red
    Write-Host ""
}

do {
    Show-Menu
    $choice = Read-Host "Enter your choice (0/1/2/3/4/5/6/7/8)"

    switch ($choice) {
        "1" {
            Write-Host ">>> Starting detection tool (Press Ctrl+C to stop)" -ForegroundColor Cyan

            $mods_folder = "D:\MCLDownload\Game\.minecraft\mods"
            $config_folder = "D:\MCLDownload\Game\.minecraft\config"
            $config_backup_folder = "D:\MCLDownload\Game\.minecraft\config_backup"
            $specified_jar = "4681704866889354274@3@0.jar"
            $mods_backup_folder = "D:\MCLDownload\Game\.minecraft\mods_backup"

            # =============================
            # Function: Delete the specified Jar file
            # =============================
            function Delete-SpecifiedJar {
                $targetPath = Join-Path -Path $mods_folder -ChildPath $specified_jar
                if (Test-Path $targetPath) {
                    Write-Host "Target jar detected: $targetPath. Deleting in 3 seconds..." -ForegroundColor Red
                    Start-Sleep -Seconds 3
                    if (Test-Path $targetPath) {
                        Remove-Item $targetPath -Force -Confirm:$false
                        Write-Host "Deleted: $targetPath" -ForegroundColor Red
                    }
                }
            }

            # =============================
            # Function: Restore deleted Jar files from mods_backup
            # =============================
            function Restore-DeletedJars {
                if (Test-Path $mods_backup_folder) {
                    $backupJars = Get-ChildItem -Path $mods_backup_folder -Filter *.jar
                    if ($backupJars.Count -gt 0) {
                        Write-Host ">>> Detected missing jar(s), restoring all jars from backup..." -ForegroundColor Yellow
                        foreach ($jar in $backupJars) {
                            $source = $jar.FullName
                            $destination = Join-Path -Path $mods_folder -ChildPath $jar.Name
                            Write-Host "Restoring: $($jar.Name)" -ForegroundColor Green
                            Copy-Item -Path $source -Destination $destination -Force
                        }
                        Write-Host ">>> All missing jars restored from backup." -ForegroundColor Green
                    } else {
                        Write-Host "No backup jars found in $mods_backup_folder." -ForegroundColor DarkGray
                    }
                } else {
                    Write-Host "Backup folder does not exist: $mods_backup_folder. Cannot restore jars." -ForegroundColor Red
                }
            }

            # =============================
            # Function: Backup config files from config to config_backup
            # =============================
            function Backup-ConfigFiles {
                if (-not (Test-Path $config_backup_folder)) {
                    New-Item -ItemType Directory -Path $config_backup_folder | Out-Null
                }
                # Define the types of configuration files to backup
                $configTypes = @("*.json", "*.cfg", "*.txt", "*.xml", "*.properties")
                foreach ($type in $configTypes) {
                    Get-ChildItem -Path $config_folder -Filter $type | ForEach-Object {
                        $source = $_.FullName
                        $backup = Join-Path -Path $config_backup_folder -ChildPath $_.Name
                        if (-not (Test-Path $backup) -or (Get-Item $source).LastWriteTime -gt (Get-Item $backup).LastWriteTime) {
                            Write-Host "Backing up config file: $($_.Name)" -ForegroundColor Yellow
                            Copy-Item -Path $source -Destination $backup -Force
                        }
                    }
                }
            }

            # =============================
            # Function: Restore config files from config_backup to config
            # =============================
            function Restore-ConfigFiles {
                if (Test-Path $config_backup_folder) {
                    # Define the types of configuration files to restore
                    $configTypes = @("*.json", "*.cfg", "*.txt", "*.xml", "*.properties")
                    foreach ($type in $configTypes) {
                        Get-ChildItem -Path $config_backup_folder -Filter $type | ForEach-Object {
                            $backup = $_.FullName
                            $destination = Join-Path -Path $config_folder -ChildPath $_.Name
                            Write-Host "Restoring config file: $($_.Name)" -ForegroundColor Green
                            Copy-Item -Path $backup -Destination $destination -Force
                        }
                    }
                } else {
                    Write-Host "Config backup folder does not exist: $config_backup_folder. Cannot restore configs." -ForegroundColor Red
                }
            }

            # =============================
            # Function: Check if Java process is running (if needed)
            # =============================
            function Check-ProcessRunning {
                Get-Process -Name "java" -ErrorAction SilentlyContinue
            }

            # =============================
            # Main Logic for Option 1
            # =============================
            try {
                $loopCount = 0
                $maxLoops = 5
                $intervalSeconds = 2

                while ($true) {
                    # 1. Delete the specified Jar file
                    Delete-SpecifiedJar

                    # 2. Check Java process and backup/restore config files if needed
                    if (Check-ProcessRunning) {
                        Backup-ConfigFiles
                        Restore-ConfigFiles
                    }

                    # 3. Loop to backup and restore config files every 2 seconds, 5 times
                    if ($loopCount -lt $maxLoops) {
                        Write-Host ">>> Loop $loopCount : Backing up and restoring config files..." -ForegroundColor Cyan
                        Backup-ConfigFiles
                        Restore-ConfigFiles
                        $loopCount++
                        Start-Sleep -Seconds $intervalSeconds
                    } else {
                        # Reset loop counter to continue the cycle
                        $loopCount = 0
                    }

                    # 4. Restore any missing Jar files from mods_backup
                    Restore-DeletedJars

                    # 5. Sleep for a short interval to prevent high CPU usage
                    Start-Sleep -Seconds 1
                }
            } catch {
                Write-Host "An error occurred: $_" -ForegroundColor Red
            }
        }
        "2" {
            Write-Host ">>> Starting backup of mods folder..." -ForegroundColor Cyan

            $mods_folder = "D:\MCLDownload\Game\.minecraft\mods"
            $mods_backup_folder = "D:\MCLDownload\Game\.minecraft\mods_backup"

            if (-not (Test-Path $mods_backup_folder)) {
                New-Item -ItemType Directory -Path $mods_backup_folder | Out-Null
            }

            Get-ChildItem -Path $mods_folder -Filter *.jar | ForEach-Object {
                $source = $_.FullName
                $backup = "$mods_backup_folder\$($_.Name)"
                if (-not (Test-Path $backup)) {
                    Copy-Item $source -Destination $backup -Force
                    Write-Host "Backed up: $($_.Name)" -ForegroundColor Yellow
                } else {
                    Write-Host "Backup already exists: $($_.Name)" -ForegroundColor DarkGray
                }
            }

            Write-Host ">>> Mods backup complete!" -ForegroundColor Green
            Pause
        }
        "3" {
            Write-Host ">>> Opening mods folder..." -ForegroundColor Cyan
            Start-Process "explorer.exe" "D:\MCLDownload\Game\.minecraft\mods"
            Write-Host "Operation complete, press any key to return to the menu..." -ForegroundColor Yellow
            Pause
        }
        "4" {
            Write-Host ">>> Opening .minecraft folder..." -ForegroundColor Cyan
            Start-Process "explorer.exe" "D:\MCLDownload\Game\.minecraft"
            Write-Host "Operation complete, press any key to return to the menu..." -ForegroundColor Yellow
            Pause
        }
        "5" {
            $shaderpacks_folder = "D:\MCLDownload\Game\.minecraft\shaderpacks"
            if (-not (Test-Path $shaderpacks_folder)) {
                New-Item -ItemType Directory -Path $shaderpacks_folder | Out-Null
                Write-Host "Shaderpacks folder created successfully." -ForegroundColor Green
            } else {
                Write-Host "You already have a shaderpacks folder, meow." -ForegroundColor Yellow
            }
            Write-Host "Press any key to return to the menu..." -ForegroundColor Yellow
            Pause
        }
        "6" {
            Write-Host ">>> Opening shaderpacks folder..." -ForegroundColor Cyan
            Start-Process "explorer.exe" "D:\MCLDownload\Game\.minecraft\shaderpacks"
            Write-Host "Operation complete, press any key to return to the menu..." -ForegroundColor Yellow
            Pause
        }
        "7" {
            $mods_folder = "D:\MCLDownload\Game\.minecraft\mods"
            Write-Host "You are about to delete all .jar files in mods folder." -ForegroundColor Red
            Write-Host "Are you sure? (Yes/No)" -ForegroundColor Yellow
            $confirm = Read-Host "Enter your choice"

            if ($confirm -eq "Yes" -or $confirm -eq "yes") {
                Get-ChildItem -Path $mods_folder -Filter *.jar | ForEach-Object {
                    Remove-Item $_.FullName -Force -Confirm:$false
                    Write-Host "Deleted: $($_.Name)" -ForegroundColor Red
                }
                Write-Host "All mods have been deleted." -ForegroundColor Red
            } else {
                Write-Host "Operation canceled." -ForegroundColor Green
            }
            Write-Host "Press any key to return to the menu..." -ForegroundColor Yellow
            Pause
        }
        "8" {
            Write-Host ">>> Restoring mods from backup..." -ForegroundColor Cyan

            $mods_folder = "D:\MCLDownload\Game\.minecraft\mods"
            $mods_backup_folder = "D:\MCLDownload\Game\.minecraft\mods_backup"

            if (-not (Test-Path $mods_backup_folder)) {
                Write-Host "Backup folder does not exist, unable to restore." -ForegroundColor Red
                Pause
                return
            }

            $backup_files = Get-ChildItem -Path $mods_backup_folder -Filter *.jar

            if ($backup_files.Count -eq 0) {
                Write-Host "No backup files found in the backup folder." -ForegroundColor Red
                Pause
                return
            }

            foreach ($file in $backup_files) {
                $source = $file.FullName
                $destination = "$mods_folder\$($file.Name)"
                if (-not (Test-Path $destination)) {
                    Copy-Item -Path $source -Destination $destination -Force
                    Write-Host "Restored: $($file.Name)" -ForegroundColor Green
                } else {
                    Write-Host "$($file.Name) already exists in the mods folder. Skipping..." -ForegroundColor Yellow
                }
            }

            Write-Host ">>> Restore process completed!" -ForegroundColor Green
            Pause
        }
        "0" {
            Write-Host "Exiting tool..." -ForegroundColor Red
            break
        }
        default {
            Write-Host "Invalid choice, please enter a valid option." -ForegroundColor Red
        }
    }
} while ($choice -ne "0")