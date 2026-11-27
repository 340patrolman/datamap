# T-GIS signal sheet PDF -> PNG (WinRT Pdf) -> Windows OCR (ko) -> JSON words with boxes
# usage: powershell -File tgis-ocr.ps1 -Pdf <abs pdf> -Out <abs json> [-Scale 3] [-Png <abs png>]
param([string]$Pdf = '', [string]$Out, [double]$Scale = 3, [string]$Png = '', [string]$Img = '')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]
$null = [Windows.Storage.FileAccessMode, Windows.Storage, ContentType = WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) { $m = $asTask.MakeGenericMethod($t); $task = $m.Invoke($null, @($op)); $task.Wait() | Out-Null; $task.Result }
$asAct = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' })[0]
function AwaitA($op) { $task = $asAct.Invoke($null, @($op)); $task.Wait() | Out-Null }
function OcrBmp($bmp) {
  $r = Await ($eng.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult]); $words = @()
  foreach ($ln in $r.Lines) { foreach ($w in $ln.Words) { $b = $w.BoundingRect; $words += , @($w.Text, [int]$b.X, [int]$b.Y, [int]$b.Width, [int]$b.Height) } }
  return $words
}
if ($Img -ne '') {
  $eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage((New-Object Windows.Globalization.Language('ko')))
  $res = @()
  foreach ($one in $Img.Split('|')) {
    $f2 = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($one)) ([Windows.Storage.StorageFile])
    $s2 = Await ($f2.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    $dec = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($s2)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bmp = Await ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    $res += @{ page = 0; src = $one; w = $bmp.PixelWidth; h = $bmp.PixelHeight; words = (OcrBmp $bmp) }
    $s2.Dispose()
  }
  [System.IO.File]::WriteAllText($Out, (ConvertTo-Json -InputObject $res -Depth 6 -Compress), (New-Object System.Text.UTF8Encoding($false)))
  Write-Output ('ok imgs ' + $res.Count); exit 0
}
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($Pdf)) ([Windows.Storage.StorageFile])
$doc = Await ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
$eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage((New-Object Windows.Globalization.Language('ko')))
$res = @()
for ($i = 0; $i -lt $doc.PageCount; $i++) {
  $pg = $doc.GetPage($i)
  $opt = New-Object Windows.Data.Pdf.PdfPageRenderOptions
  $opt.DestinationWidth = [uint32]($pg.Size.Width * $Scale); $opt.DestinationHeight = [uint32]($pg.Size.Height * $Scale)
  $st = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
  AwaitA ($pg.RenderToStreamAsync($st, $opt))
  if ($Png -ne '' -and $i -eq 0) {
    $st.Seek(0); $rd = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($st); $fs = [System.IO.File]::Create($Png); $rd.CopyTo($fs); $fs.Close()
  }
  $st.Seek(0)
  $dec = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($st)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bmp = Await ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  if ($bmp.PixelWidth -gt [Windows.Media.Ocr.OcrEngine]::MaxImageDimension -or $bmp.PixelHeight -gt [Windows.Media.Ocr.OcrEngine]::MaxImageDimension) { $res += @{ page = $i; err = 'too big ' + $bmp.PixelWidth + 'x' + $bmp.PixelHeight }; continue }
  $r = Await ($eng.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
  $words = @()
  foreach ($ln in $r.Lines) { foreach ($w in $ln.Words) { $b = $w.BoundingRect; $words += , @($w.Text, [int]$b.X, [int]$b.Y, [int]$b.Width, [int]$b.Height) } }
  $res += @{ page = $i; w = $bmp.PixelWidth; h = $bmp.PixelHeight; words = $words }
}
$json = ConvertTo-Json -InputObject $res -Depth 6 -Compress
[System.IO.File]::WriteAllText($Out, $json, (New-Object System.Text.UTF8Encoding($false)))
Write-Output ('ok pages ' + $doc.PageCount)
