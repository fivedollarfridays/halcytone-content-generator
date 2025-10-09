# SSH Key Setup Script for Windows
# Run this in PowerShell to create SSH key for cloud server access

Write-Host "🔑 Creating SSH Key for Cloud Server..." -ForegroundColor Green

# Check if .ssh directory exists
$sshDir = "$env:USERPROFILE\.ssh"
if (-not (Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir | Out-Null
    Write-Host "✅ Created .ssh directory" -ForegroundColor Green
}

# Generate SSH key
$keyPath = "$sshDir\toombos_rsa"
if (Test-Path $keyPath) {
    Write-Host "⚠️  SSH key already exists at: $keyPath" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to overwrite? (y/n)"
    if ($overwrite -ne "y") {
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit
    }
}

# Generate the key
Write-Host "Generating SSH key pair..." -ForegroundColor Cyan
ssh-keygen -t rsa -b 4096 -f $keyPath -N '""' -C "toombos-deployment"

Write-Host ""
Write-Host "✅ SSH Key Created Successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Your PUBLIC KEY (copy this to DigitalOcean):" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Gray
Get-Content "$keyPath.pub"
Write-Host "================================================" -ForegroundColor Gray
Write-Host ""
Write-Host "💾 Keys saved to:" -ForegroundColor Yellow
Write-Host "   Private: $keyPath" -ForegroundColor White
Write-Host "   Public:  $keyPath.pub" -ForegroundColor White
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Green
Write-Host "   1. Copy the PUBLIC KEY above" -ForegroundColor White
Write-Host "   2. In DigitalOcean, paste it when creating your Droplet" -ForegroundColor White
Write-Host "   3. After creating the Droplet, note the IP address" -ForegroundColor White
Write-Host ""

# Copy to clipboard if possible
try {
    Get-Content "$keyPath.pub" | Set-Clipboard
    Write-Host "✅ Public key copied to clipboard!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not copy to clipboard. Please copy manually." -ForegroundColor Yellow
}

pause
