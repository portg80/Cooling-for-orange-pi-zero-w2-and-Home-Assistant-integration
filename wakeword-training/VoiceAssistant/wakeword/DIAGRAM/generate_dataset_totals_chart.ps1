Add-Type -AssemblyName System.Drawing

$width = 1200
$height = 800

$bmp = New-Object System.Drawing.Bitmap($width, $height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$g.Clear([System.Drawing.Color]::White)

$titleFont = New-Object System.Drawing.Font("Arial", 26)
$labelFont = New-Object System.Drawing.Font("Arial", 16)
$valueFont = New-Object System.Drawing.Font("Arial", 16)
$axisFont = New-Object System.Drawing.Font("Arial", 14)

$blackBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::Black)
$gridPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(225, 225, 225), 1)
$axisPen = New-Object System.Drawing.Pen([System.Drawing.Color]::Black, 2)

$plotLeft = 110
$plotTop = 90
$plotWidth = 980
$plotHeight = 570
$plotBottom = $plotTop + $plotHeight
$plotRight = $plotLeft + $plotWidth

$title = "Сравнение суммарных часов"
$g.DrawString($title, $titleFont, $blackBrush, 330, 28)

$values = @(0.6333333333, 23.0861111111, 25.8277777778)
$labels = @(
    @("Базовые", "позитивы"),
    @("Аугментированные", "позитивы"),
    @("Негативы")
)
$barBrushes = @(
    (New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(91, 192, 222))),
    (New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(31, 119, 180))),
    (New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 127, 14)))
)

$maxValue = 30.0
$yticks = @(0, 5, 10, 15, 20, 25, 30)

foreach ($tick in $yticks) {
    $y = [int]($plotBottom - ($tick / $maxValue) * $plotHeight)
    $g.DrawLine($gridPen, $plotLeft, $y, $plotRight, $y)
    $g.DrawString([string]$tick, $axisFont, $blackBrush, 62, $y - 10)
}

$g.DrawLine($axisPen, $plotLeft, $plotTop, $plotLeft, $plotBottom)
$g.DrawLine($axisPen, $plotLeft, $plotBottom, $plotRight, $plotBottom)

$barWidth = 220
$gap = 90
$firstX = $plotLeft + 95

for ($i = 0; $i -lt $values.Count; $i++) {
    $x = [int]($firstX + $i * ($barWidth + $gap))
    $barHeight = ($values[$i] / $maxValue) * $plotHeight
    $y = [int]($plotBottom - $barHeight)
    $h = [int]$barHeight

    $g.FillRectangle($barBrushes[$i], $x, $y, $barWidth, $h)
    $g.DrawRectangle($axisPen, $x, $y, $barWidth, $h)

    $valueText = ("{0:N3} ч" -f $values[$i]).Replace(",", ".")
    $valueSize = $g.MeasureString($valueText, $valueFont)
    $g.DrawString($valueText, $valueFont, $blackBrush, $x + ($barWidth - $valueSize.Width) / 2, $y - 30)

    $lineY = $plotBottom + 14
    foreach ($line in $labels[$i]) {
        $lineSize = $g.MeasureString($line, $labelFont)
        $g.DrawString($line, $labelFont, $blackBrush, $x + ($barWidth - $lineSize.Width) / 2, $lineY)
        $lineY += 22
    }
}

$g.TranslateTransform(35, 400)
$g.RotateTransform(-90)
$g.DrawString("Часы", $labelFont, $blackBrush, 0, 0)
$g.ResetTransform()

$repoRoot = Split-Path -Parent $PSScriptRoot
$outPaths = @(
    "E:\LABS_VOLGU\WakeWord_Neiro\data\_dataset_stats\totals_pos_vs_neg.png",
    (Join-Path $repoRoot "fig\\totals_pos_vs_neg.png")
)

foreach ($outPath in $outPaths) {
    $bmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
}

$axisPen.Dispose()
$gridPen.Dispose()
$blackBrush.Dispose()
$titleFont.Dispose()
$labelFont.Dispose()
$valueFont.Dispose()
$axisFont.Dispose()
foreach ($brush in $barBrushes) {
    $brush.Dispose()
}
$g.Dispose()
$bmp.Dispose()
