# Read-only motor media inventory

This scanner reads metadata from `D:\Lily\Ankarsrum\Company Knowledge Hub` and its
ordinary subfolders. It never moves, renames, overwrites, deletes, or opens the content
of source photos/videos. It writes only a new CSV outside the source tree.

## Windows

1. Download and extract the repository ZIP outside the source folder.
2. Double-click **inventory-windows.cmd**. It uses an existing Python installation;
   if Python is missing, it prints the official download address. No API key, FFmpeg,
   video setup, or third-party Python package is required.
3. The report is created in `C:\Users\24463\OneDrive\Video` with a timestamp in its
   filename. That folder must already exist. Successful scans open Explorer with
   the CSV selected. Existing reports are never replaced.
4. In Notion, open Video Project and use **Import → CSV**, selecting the new report.
   Rename the new database **Motor Media Inventory**. UI wording can vary.
   This imports a new inventory; it does not automatically update or deduplicate a
   previous import. Import each report only once unless creating a separate version.
5. If useful, set Suggested category and Review status to Select properties in Notion.
   Review entries before treating any category as confirmed.

## Interpretation

- Categories: Design, Prototyping, Lab, Manufacturing, To Review.
- A unique recognized **folder** clue may suggest a category. This is tentative, not
  proof. No category is inferred from the filename alone.
- Missing or conflicting clues produce **To Review**.
- Every row is **Needs review**, because visual inspection has not been authorized
  or performed. No artificial numeric confidence score is assigned.
- Original path and relative path identify the file; local Windows paths are not
  OneDrive sharing links and generally cannot be opened from another computer.
- Size, extension, and modified UTC come from file metadata. Other formats are
  ignored. Photos include common RAW formats; videos include common camera formats.
- Symlinks and reparse directories (including junctions and some cloud directories)
  are skipped to avoid following another location. Permission/listing failures are
  recorded as Scan issue rows. Any such rows mean the scan is incomplete.
- The CSV uses UTF-8 with BOM for Windows/Excel. Potential spreadsheet formulas are
  prefixed with an apostrophe; Original path preserves the file's exact identity.
- Concurrent changes made by other programs during a scan can affect results.
- A fatal write error may leave a partial new CSV. The tool preserves it and never
  deletes or overwrites it; choose another report name on a subsequent run.

Command-line usage:

```powershell
py -3 media_inventory.py --source "D:\Lily\Ankarsrum\Company Knowledge Hub" --output "C:\Users\24463\OneDrive\Video\motor-media-inventory.csv"
```

The cloud cannot access your D: drive. You must run this scanner locally. No actual
company inventory or Notion database has been created by preparing this tool.
Direct Notion creation remains unavailable until a usable editing connection exists.
