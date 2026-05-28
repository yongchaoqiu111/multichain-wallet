# 忽略SSL证书验证
add-type @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(
            ServicePoint srvPoint, X509Certificate certificate,
            WebRequest request, int certificateProblem) {
            return true;
        }
    }
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy

$body = @{
    address = '0xTestAddress123456789'
    chain = 'ETH'
    encrypted_data = 'dGVzdGRhdGFlbmNyeXB0ZWQ='
} | ConvertTo-Json

Write-Host "发送的数据:"
Write-Host $body
Write-Host ""

try {
    $r = Invoke-WebRequest -Uri 'https://api.ai656.top/api/wallet/backup' -Method POST -Body $body -ContentType 'application/json'
    Write-Host "状态码: $($r.StatusCode)"
    Write-Host "响应内容:"
    Write-Host $r.Content
} catch {
    Write-Host "错误信息:"
    Write-Host $_.Exception.Message
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "服务器响应: $responseBody"
    }
}
