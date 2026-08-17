using System;
using System.IO;
using System.IO.Compression;

public static class UnzipShim
{
    public static int Main(string[] args)
    {
        try
        {
            if (args.Length < 2) return 2;
            string mode = args[0];
            string archive = args[1];
            using (ZipArchive zip = ZipFile.OpenRead(archive))
            {
                if (mode == "-Z1")
                {
                    foreach (ZipArchiveEntry entry in zip.Entries)
                        Console.Out.WriteLine(entry.FullName);
                    return 0;
                }
                if (mode == "-p" && args.Length >= 3)
                {
                    ZipArchiveEntry entry = zip.GetEntry(args[2]);
                    if (entry == null) return 3;
                    using (Stream input = entry.Open())
                    using (Stream output = Console.OpenStandardOutput())
                        input.CopyTo(output);
                    return 0;
                }
            }
            return 2;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex.Message);
            return 1;
        }
    }
}
