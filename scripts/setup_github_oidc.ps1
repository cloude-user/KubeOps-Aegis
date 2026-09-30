<#
.SYNOPSIS
    Script to set up Azure Entra ID OIDC Federated Identity for GitHub Actions CI/CD.
    Eliminates long-lived client secrets for GitHub Actions Terraform deployment.

.NOTES
    Prerequisites: Azure CLI installed and authenticated (az login).
#>

param(
    [string]$SubscriptionId = "YOUR_AZURE_SUBSCRIPTION_ID",
    [string]$ResourceGroupName = "rg-aegis-ops-prd",
    [string]$AppName = "app-github-actions-aegis",
    [string]$GitHubOrg = "cloude-user",
    [string]$GitHubRepo = "cloudnative-ai-ops",
    [string]$Branch = "main"
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Setting up Azure Entra ID OIDC for GitHub Actions CI/CD..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Set Active Azure Subscription
az account set --subscription $SubscriptionId

# 2. Create Azure AD Application for GitHub Actions
Write-Host "Creating Azure AD Application registration: $AppName..." -ForegroundColor Yellow
$app = az ad app create --display-name $AppName | ConvertFrom-Json
$appId = $app.appId

# 3. Create Service Principal for the App
Write-Host "Creating Service Principal for Application ID: $appId..." -ForegroundColor Yellow
$sp = az ad sp create --id $appId | ConvertFrom-Json
$spId = $sp.id

# 4. Assign Contributor Role on Subscription
Write-Host "Assigning 'Contributor' role on Subscription $SubscriptionId..." -ForegroundColor Yellow
az role assignment create --assignee $appId --role "Contributor" --scope "/subscriptions/$SubscriptionId"

# 5. Create OIDC Federated Identity Credential for GitHub Actions
$subject = "repo:${GitHubOrg}/${GitHubRepo}:ref:refs/heads/${Branch}"
Write-Host "Configuring OIDC Federated Credential for subject: $subject..." -ForegroundColor Yellow

$federatedCredential = @{
    name = "github-actions-main-branch"
    issuer = "https://token.actions.githubusercontent.com"
    subject = $subject
    description = "GitHub Actions OIDC authentication for main branch deployments"
    audiences = @("api://AzureADTokenExchange")
} | ConvertTo-Json -Depth 5

$tempFile = [System.IO.Path]::GetTempFileName()
$federatedCredential | Out-File -FilePath $tempFile -Encoding utf8

az ad app federated-credential create --id $appId --parameters $tempFile
Remove-Item -Path $tempFile -Force

# 6. Fetch Tenant ID
$tenantId = (az account show | ConvertFrom-Json).tenantId

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "SUCCESS! Azure OIDC Credentials successfully configured!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Add the following secrets to your GitHub Repository ($GitHubOrg/$GitHubRepo):" -ForegroundColor White
Write-Host "  AZURE_CLIENT_ID       : $appId" -ForegroundColor Yellow
Write-Host "  AZURE_TENANT_ID       : $tenantId" -ForegroundColor Yellow
Write-Host "  AZURE_SUBSCRIPTION_ID : $SubscriptionId" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Green
