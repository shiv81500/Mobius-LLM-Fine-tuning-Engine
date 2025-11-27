$sourceDir = "data/gguf"
$targetBase = "lmstudio_models"
$author = "local-user"

# Get the latest GGUF file
$ggufFile = Get-ChildItem -Path $sourceDir -Filter "*.gguf" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($ggufFile) {
    # Use the filename (without extension) as the model name
    $modelName = $ggufFile.BaseName
    
    # Create the structure Author/ModelName
    $targetDir = Join-Path $targetBase "$author\$modelName"
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

    $destPath = Join-Path $targetDir "$ggufFile.Name"
    Copy-Item -Path $ggufFile.FullName -Destination $destPath
    
    Write-Host "=================================================="
    Write-Host "SUCCESS! Model prepared for LM Studio."
    Write-Host "Model Name: $modelName"
    Write-Host "=================================================="
    Write-Host "1. Open LM Studio."
    Write-Host "2. Go to the 'My Models' (folder icon) tab."
    Write-Host "3. Click 'Change Path' (or 'Add Path')."
    Write-Host "4. Select this folder:"
    Write-Host (Resolve-Path $targetBase).Path
    Write-Host "=================================================="
} else {
    Write-Host "Error: No GGUF file found in $sourceDir"
}
