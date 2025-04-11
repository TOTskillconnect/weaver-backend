# PowerShell script to test the API endpoints
$ErrorActionPreference = "Stop"
$baseUrl = "http://localhost:5000"

# Helper function to format response output
function Format-Response {
    param (
        [string]$endpoint,
        [object]$response,
        [double]$duration
    )
    Write-Host "`nEndpoint: " -NoNewline
    Write-Host $endpoint -ForegroundColor Cyan
    Write-Host "Status: " -NoNewline
    Write-Host $response.StatusCode -ForegroundColor $(If ($response.StatusCode -eq 200) { "Green" } Else { "Red" })
    Write-Host "Duration: " -NoNewline
    Write-Host "$($duration.ToString("0.00"))s" -ForegroundColor Yellow
    Write-Host "Response: " -NoNewline
    
    try {
        $content = $response.Content | ConvertFrom-Json
        Write-Host ($content | ConvertTo-Json)
    }
    catch {
        Write-Host $response.Content
    }
}

# Helper function to make HTTP requests with timing
function Invoke-TimedRequest {
    param (
        [string]$endpoint,
        [string]$method = "GET",
        [object]$body = $null,
        [string]$contentType = "application/json"
    )
    
    try {
        $start = Get-Date
        $params = @{
            Uri = "$baseUrl$endpoint"
            Method = $method
            ContentType = $contentType
        }
        
        if ($body) {
            $params.Body = ($body | ConvertTo-Json)
        }
        
        $response = Invoke-WebRequest @params
        $duration = (Get-Date) - $start
        
        Format-Response -endpoint $endpoint -response $response -duration $duration.TotalSeconds
        return $true
    }
    catch {
        Write-Host "`nEndpoint: " -NoNewline
        Write-Host $endpoint -ForegroundColor Cyan
        Write-Host "Error: " -NoNewline
        Write-Host $_.Exception.Message -ForegroundColor Red
        
        # Print detailed error response if available
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $reader.BaseStream.Position = 0
            $reader.DiscardBufferedData()
            $responseBody = $reader.ReadToEnd()
            Write-Host "Error Details: " -NoNewline
            try {
                $errorJson = $responseBody | ConvertFrom-Json
                Write-Host ($errorJson | ConvertTo-Json)
            }
            catch {
                Write-Host $responseBody
            }
        }
        return $false
    }
}

Write-Host "Starting API Tests..." -ForegroundColor Green
Write-Host "===================="

# Test 1: Health Check
Write-Host "`nTest 1: Health Check" -ForegroundColor Yellow
$healthResult = Invoke-TimedRequest -endpoint "/health"

# Test 2: Submit with valid URL
Write-Host "`nTest 2: Submit with valid URL" -ForegroundColor Yellow
$validBody = @{
    url = "https://www.ycombinator.com/jobs"
    format = "json"
}
$submitResult = Invoke-TimedRequest -endpoint "/submit" -method "POST" -body $validBody

# Test 3: Submit with invalid URL
Write-Host "`nTest 3: Submit with invalid URL" -ForegroundColor Yellow
$invalidBody = @{
    url = "not-a-valid-url"
    format = "json"
}
$invalidResult = Invoke-TimedRequest -endpoint "/submit" -method "POST" -body $invalidBody

# Test 4: Submit with missing URL
Write-Host "`nTest 4: Submit with missing URL" -ForegroundColor Yellow
$missingBody = @{
    format = "json"
}
$missingResult = Invoke-TimedRequest -endpoint "/submit" -method "POST" -body $missingBody

# Summary
Write-Host "`nTest Summary" -ForegroundColor Green
Write-Host "===========" 
Write-Host "Health Check: " -NoNewline
Write-Host $(If ($healthResult) { "PASSED" } Else { "FAILED" }) -ForegroundColor $(If ($healthResult) { "Green" } Else { "Red" })
Write-Host "Valid Submit: " -NoNewline
Write-Host $(If ($submitResult) { "PASSED" } Else { "FAILED" }) -ForegroundColor $(If ($submitResult) { "Green" } Else { "Red" })
Write-Host "Invalid URL: " -NoNewline
Write-Host $(If (-not $invalidResult) { "PASSED" } Else { "FAILED" }) -ForegroundColor $(If (-not $invalidResult) { "Green" } Else { "Red" })
Write-Host "Missing URL: " -NoNewline
Write-Host $(If (-not $missingResult) { "PASSED" } Else { "FAILED" }) -ForegroundColor $(If (-not $missingResult) { "Green" } Else { "Red" }) 