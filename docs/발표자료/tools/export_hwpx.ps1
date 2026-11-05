param([string]$DocsRoot = (Join-Path $PSScriptRoot '..\..'))
$ErrorActionPreference = 'Stop'
$docs = (Resolve-Path $DocsRoot).Path
$files = @(Get-ChildItem -LiteralPath $docs -Filter '*.hwpx') +
         @(Get-ChildItem -LiteralPath (Join-Path $docs '산출물') -Filter '*.hwpx')
$taskTempPath = Join-Path ([IO.Path]::GetTempPath()) ('picktiming-hwpx-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskTempPath | Out-Null
$results = @()
for ($i = 0; $i -lt $files.Count; $i++) {
    $file = $files[$i]
    $inputFile = Join-Path $taskTempPath "$i.hwpx"
    $savedFile = Join-Path $taskTempPath "$i.saved.hwpx"
    $pdfFile = Join-Path $taskTempPath "$i.pdf"
    Copy-Item -LiteralPath $file.FullName -Destination $inputFile
    $hwp = New-Object -ComObject HWPFrame.HwpObject
    try {
        # 형식은 한글이 자동 판별하도록 한다. readonly 인자는 이 설치에서 RPC 오류를 일으킨다.
        if (-not $hwp.Open($inputFile, '', '')) { throw "Cannot open $($file.Name)" }
        if (-not $hwp.SaveAs($savedFile, 'HWPX', '')) { throw "Cannot save HWPX $($file.Name)" }
        if (-not $hwp.SaveAs($pdfFile, 'PDF', '')) { throw "Cannot export PDF $($file.Name)" }
    }
    finally {
        $hwp.Quit()
    }
    $relative = $file.FullName.Substring($docs.Length + 1)
    $destination = Join-Path (Join-Path $docs 'pdf') ([IO.Path]::ChangeExtension($relative, '.pdf'))
    Copy-Item -LiteralPath $savedFile -Destination $file.FullName -Force
    Copy-Item -LiteralPath $pdfFile -Destination $destination -Force
    $results += [PSCustomObject]@{HWPX=$relative; Opened=$true; NativeSaved=$true; PDF=$destination}
    Write-Output "Exported $($file.Name)"
}
$results | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $docs '발표자료\hwpx-check.json')
