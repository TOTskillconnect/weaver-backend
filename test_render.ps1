# Test script for Render backend
$baseUrl = "https://weaver-backend.onrender.com"

Write-Host "Testing Backend Connection..." -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green

# Test health endpoint
Write-Host "`nTesting Health Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    Write-Host "Health Check Response:" -ForegroundColor Cyan
    $response | ConvertTo-Json
} catch {
    Write-Host "Error accessing health endpoint: $_" -ForegroundColor Red
}

# Test submit endpoint
Write-Host "`nTesting Submit Endpoint..." -ForegroundColor Yellow
$body = @{
    url = "https://www.ycombinator.com/jobs"
    format = "json"
} | ConvertTo-Json

try {
    $headers = @{
        "Content-Type" = "application/json"
    }
    $response = Invoke-RestMethod -Uri "$baseUrl/submit" -Method Post -Body $body -Headers $headers
    Write-Host "Submit Response:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 4
} catch {
    Write-Host "Error accessing submit endpoint: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host "Error Details:" -ForegroundColor Red
        $responseBody
    }
} 