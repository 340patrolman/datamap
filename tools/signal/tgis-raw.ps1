# T-GIS signal sheet PDFs -> raw OCR words for ko and en-US at scale 3 and 4, one process for many files
# usage: powershell -File tgis-raw.ps1 -List <utf8 tsv: pdf<TAB>outbase>    writes <outbase>.<ko|en>.s<3|4>.json  (skips existing)
param([string]$List)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) { $m = $asTask.MakeGenericMethod($t); $task = $m.Invoke($null, @($op)); $task.Wait() | Out-Null; $task.Result }
$asAct = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' })[0]
function AwaitA($op) { $task = $asAct.Invoke($null, @($op)); $task.Wait() | Out-Null }
$eng = @{ ko = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage((New-Object Windows.Globalization.Language('ko'))); en = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage((New-Object Windows.Globalization.Language('en-US'))) }
$n = 0
foreach ($line in [System.IO.File]::ReadAllLines($List, [System.Text.Encoding]::UTF8)) {
  if ($line -eq '') { continue }
  $pdf, $base = $line.Split("`t")
  try {
    if (Test-Path "$base.en.s4.json") { continue }
    $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($pdf)) ([Windows.Storage.StorageFile])
    $doc = Await ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
    $pg = $doc.GetPage(0)
    foreach ($s in 3, 4) {
      $opt = New-Object Windows.Data.Pdf.PdfPageRenderOptions
      $opt.DestinationWidth = [uint32]($pg.Size.Width * $s); $opt.DestinationHeight = [uint32]($pg.Size.Height * $s)
      $st = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
      AwaitA ($pg.RenderToStreamAsync($st, $opt))
      $st.Seek(0)
      $dec = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($st)) ([Windows.Graphics.Imaging.BitmapDecoder])
      $bmp = Await ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
      foreach ($k in 'ko', 'en') {
        $r = Await ($eng[$k].RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
        $words = @()
        foreach ($ln in $r.Lines) { foreach ($w in $ln.Words) { $b = $w.BoundingRect; $words += , @($w.Text, [int]$b.X, [int]$b.Y, [int]$b.Width, [int]$b.Height) } }
        $json = ConvertTo-Json -InputObject @(@{ page = 0; w = $bmp.PixelWidth; h = $bmp.PixelHeight; words = $words }) -Depth 6 -Compress
        [System.IO.File]::WriteAllText("$base.$k.s$s.json", $json, (New-Object System.Text.UTF8Encoding($false)))
      }
      $st.Dispose()
    }
    $n++; Write-Output ("ok $n " + (Split-Path $base -Leaf))
  } catch { Write-Output ("err " + (Split-Path $base -Leaf) + " " + $_.Exception.Message) }
}
Write-Output "done $n"
