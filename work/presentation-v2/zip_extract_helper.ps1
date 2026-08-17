param(
  [Alias('Z1')][switch]$List,
  [Alias('p')][switch]$Print,
  [Parameter(Position=0)][string]$Archive,
  [Parameter(Position=1)][string]$Entry
)

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($Archive)
try {
  if ($List) {
    foreach ($item in $zip.Entries) {
      [Console]::Out.WriteLine($item.FullName)
    }
    exit 0
  }
  if ($Print) {
    $item = $zip.GetEntry($Entry)
    if ($null -eq $item) { throw "Archive entry not found: $Entry" }
    $inputStream = $item.Open()
    try {
      $outputStream = [Console]::OpenStandardOutput()
      $buffer = New-Object byte[] 65536
      while (($read = $inputStream.Read($buffer, 0, $buffer.Length)) -gt 0) {
        $outputStream.Write($buffer, 0, $read)
      }
      $outputStream.Flush()
    } finally {
      $inputStream.Dispose()
    }
    exit 0
  }
  throw 'Unsupported unzip mode'
} finally {
  $zip.Dispose()
}
