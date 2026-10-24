# Read-only motor media inventory

This scanner reads metadata from `D:\Lily\Ankarsrum\Company Knowledge Hub` and its
ordinary subfolders. It never moves, renames, overwrites, deletes, or opens the content
of source photos/videos. It writes only a new CSV outside the source tree.

## Windows

1. Download and extract the repository ZIP outside the source folder.
2. Double-click **inventory-windows.cmd**. It uses built-in Windows PowerShell 5.1;
   Python and extra packages are not required. No API key or video setup is required.
   Keep inventory-windows.ps1 beside the launcher. If Windows blocks the downloaded
   script, review it, then right-click it → Properties → Unblock if permitted by your
   company. The launcher requests RemoteSigned for its process only; it does not
   change your persistent execution policy or override company Group Policy.
3. The report is created in `C:\Users\24463\Downloads` with a timestamp in its
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
- Symlinks and reparse entries (including junctions and some cloud placeholders)
  are skipped to avoid following another location. Permission/listing failures are
  recorded as Scan issue rows. Any such rows mean the scan is incomplete.
- The CSV uses UTF-8 with BOM for Windows/Excel. Potential spreadsheet formulas are
  prefixed with an apostrophe; Original path preserves the file's exact identity.
- Concurrent changes made by other programs during a scan can affect results.
- A fatal write error may leave a partial new CSV. The tool preserves it and never
  deletes or overwrites it; choose another report name on a subsequent run.

PowerShell command-line usage:

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\inventory-windows.ps1 -Source "D:\Lily\Ankarsrum\Company Knowledge Hub" -Output "C:\Users\24463\Downloads\motor-media-inventory.csv"
```

The cloud cannot access your D: drive. You must run this scanner locally. No actual
company inventory or Notion database has been created by preparing this tool.
Direct Notion creation remains unavailable until a usable editing connection exists.

The PowerShell script has been exercised on PowerShell 7.4 with temporary fixtures
for source preservation, category rules, overwrite refusal, skipped links, and empty
folders. Native Windows PowerShell 5.1 execution still needs validation on your PC.
The Python version remains available as an optional alternative; the Windows launcher
no longer uses it.

The default report folder is local Downloads. OneDrive may expose its folder as a
reparse point; the scanner keeps its conservative link protection and avoids using
that folder as the default output. Your source folder and existing media stay unchanged.
