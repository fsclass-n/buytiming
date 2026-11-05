param([string]$DocsRoot = (Join-Path $PSScriptRoot '..\..'))
$ErrorActionPreference = 'Stop'
$docs = (Resolve-Path $DocsRoot).Path
$source = Join-Path $docs '3조_최종발표_PPT.pptx'
$pdf = Join-Path $docs '3조_최종발표_PPT.pdf'
$ppt = New-Object -ComObject PowerPoint.Application
$deck = $null
try {
    # 작업 중인 다른 프레젠테이션을 닫거나 저장하지 않는다.
    $deck = $ppt.Presentations.Open($source, $true, $false, $false)
    $deck.SaveAs($pdf, 32)
    $issues = @()
    foreach ($slide in $deck.Slides) {
        foreach ($shape in $slide.Shapes) {
            if ($shape.HasTextFrame -and $shape.TextFrame.HasText) {
                if ($shape.TextFrame2.TextRange.BoundHeight -gt ($shape.Height + 2)) {
                    $issues += [PSCustomObject]@{
                        Slide = $slide.SlideIndex
                        Text = $shape.TextFrame.TextRange.Text
                        Actual = $shape.TextFrame2.TextRange.BoundHeight
                        Available = $shape.Height
                    }
                }
            }
        }
    }
    $report = [PSCustomObject]@{
        Renderer = 'Microsoft PowerPoint'
        Slides = $deck.Slides.Count
        TextHeightIssues = $issues
    }
    $report | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $docs '발표자료\powerpoint-check.json')
    if ($issues.Count -gt 0) { throw "Text height overflow: $($issues.Count)" }
    Copy-Item $pdf (Join-Path $docs 'pdf\프로젝트_발표자료.pdf') -Force
    Write-Output "Exported $($deck.Slides.Count) slides; text height overflow: 0"
}
finally {
    if ($null -ne $deck) { $deck.Close() }
    if ($ppt.Presentations.Count -eq 0) { $ppt.Quit() }
}
