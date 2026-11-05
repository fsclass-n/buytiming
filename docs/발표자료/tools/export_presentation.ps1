param([string]$DocsRoot = (Join-Path $PSScriptRoot '..\..'), [string]$Name = '프로젝트_발표자료')
$ErrorActionPreference = 'Stop'
$docs = (Resolve-Path $DocsRoot).Path
$source = Join-Path $docs "$Name.pptx"
$pdf = Join-Path $docs "pdf\$Name.pdf"
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
                $range = $shape.TextFrame2.TextRange
                if ($range.BoundHeight -gt ($shape.Height + 2) -or $range.BoundWidth -gt ($shape.Width + 2)) {
                    $issues += [PSCustomObject]@{
                        Slide = $slide.SlideIndex
                        Text = $shape.TextFrame.TextRange.Text
                        ActualHeight = $range.BoundHeight
                        AvailableHeight = $shape.Height
                        ActualWidth = $range.BoundWidth
                        AvailableWidth = $shape.Width
                    }
                }
            }
        }
    }
    $report = [PSCustomObject]@{
        Renderer = 'Microsoft PowerPoint'
        File = "$Name.pptx"
        Slides = $deck.Slides.Count
        TextHeightIssues = $issues
    }
    $report | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $docs "발표자료\powerpoint-check-$Name.json")
    if ($issues.Count -gt 0) { throw "Text height overflow: $($issues.Count)" }
    Write-Output "Exported $($deck.Slides.Count) slides; text height overflow: 0"
}
finally {
    if ($null -ne $deck) { $deck.Close() }
    if ($ppt.Presentations.Count -eq 0) { $ppt.Quit() }
}
