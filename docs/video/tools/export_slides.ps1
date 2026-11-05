param([string]$Deck, [string]$OutDir)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$ppt = New-Object -ComObject PowerPoint.Application
$pres = $null
try {
    # 읽기 전용으로 열어 원본을 바꾸지 않는다.
    $pres = $ppt.Presentations.Open($Deck, $true, $false, $false)
    foreach ($slide in $pres.Slides) {
        $slide.Export((Join-Path $OutDir ("slide{0:D2}.png" -f $slide.SlideIndex)), 'PNG', 1920, 1080)
    }
    Write-Output "Exported $($pres.Slides.Count) slides"
}
finally {
    if ($null -ne $pres) { $pres.Close() }
    if ($ppt.Presentations.Count -eq 0) { $ppt.Quit() }
}
