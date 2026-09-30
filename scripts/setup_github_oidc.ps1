<#
.SYNOPSIS
    Manual Azure Entra ID OIDC Federated Credential Setup for Personal GitHub Account.
    Tailored for: GitHub User: cloude-user | Repo: KubeOps-Aegis

.NOTES
    Prerequisites: Run in PowerShell logged into Azure CLI (az login).
#>

param(
    [string]$SubscriptionId = "YOUR_AZURE_SUBSCRIPTION_ID",
    [string]$AppName = "app-github-actions-kubeops",
    [string]$GitHubUser = "cloude-user",
    [string]$GitHubRepo = "KubeOps-Aegis",
    [string]$Branch = "main"
)

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Azure OIDC Setup for Personal GitHub Account: $GitHubUser/$GitHubRepo" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Set Active Azure Subscription
Write-Host "1. Setting Azure Subscription ID: $SubscriptionId..." -ForegroundColor Yellow
az account set --subscription $SubscriptionId

# 2. Register Azure AD Application
Write-Host "2. Creating Azure AD Application Registration ($AppName)..." -ForegroundColor Yellow
$app = az ad app create --display-name $AppName | ConvertFrom-Json
$appId = $app.appId
Write-Host "   Application (Client) ID: $appId" -ForegroundColor Green

# 3. Create Service Principal
Write-Host "3. Creating Azure Service Principal..." -ForegroundColor Yellow
$sp = az ad sp create --id $appId | ConvertFrom-Json

# 4. Assign Contributor Role on Azure Subscription
Write-Host "4. Assigning 'Contributor' Role on Subscription..." -ForegroundColor Yellow
az role assignment create --assignee $appId --role "Contributor" --scope "/subscriptions/$SubscriptionId"

# 5. Create Federated Identity Credential for Personal GitHub Repo
# Format for Personal Account: repo:cloude-user/KubeOps-Aegis:ref:refs/heads/main
$subject = "repo:${GitHubUser}/${GitHubRepo}:ref:refs/heads/${Branch}"
Write-Host "5. Configuring Federated OIDC Credential for: $subject..." -ForegroundColor Yellow

$federatedCredential = @{
    name = "github-personal-main-branch"
    issuer = "https://token.actions.githubusercontent.com"
    subject = $subject
    description = "OIDC Federated Credential for personal account GitHub Actions"
    audiences = @("api://AzureADTokenExchange")
} | ConvertTo-Json -Depth 5

$tempFile = [System.IO.Path]::GetTempFileName()
$federatedCredential | Out-File -FilePath $tempFile -Encoding utf8

az ad app federated-credential create --id $appId --parameters $tempFile
Remove-Item -Path $tempFile -Force

# 6. Retrieve Tenant ID
$tenantId = (az account show | ConvertFrom-Json).tenantId

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "SUCCESS! OIDC FEDERATED CREDENTIAL CREATED!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "Copy these 3 Secrets into your GitHub Repo Settings:" -ForegroundColor White
Write-Host "Repository -> Settings -> Secrets and variables -> Actions -> New repository secret:" -ForegroundColor Gray
Write-Host ""
Write-Host "  AZURE_CLIENT_ID       : $appId" -ForegroundColor Yellow
Write-Host "  AZURE_TENANT_ID       : $tenantId" -ForegroundColor Yellow
Write-Host "  AZURE_SUBSCRIPTION_ID : $SubscriptionId" -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Green
