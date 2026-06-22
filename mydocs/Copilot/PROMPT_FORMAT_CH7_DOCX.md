# PROMPT: Format Chapter 7 in Minibook DOCX to Match Chapters 1–6

## File to Edit
`/Users/pragyeshmishra/GITHUB/dc-copilot/docs/minibook_llm_rag_evaluation_dbt.docx`

## What Already Exists
- The **markdown file** `/Users/pragyeshmishra/GITHUB/dc-copilot/docs/minibook_llm_rag_evaluation_dbt.md` has the complete Chapter 7 content (17 sections, 7.1–7.17) already written.
- The **docx file** has Chapters 1–6 beautifully formatted with colors, styled code blocks, borders, and professional typography. Chapter 7 was inserted into the docx but looks terrible — formatting is broken/gibberish. It needs to be **completely removed and redone from scratch**.

## YOUR TASK

1. **Open the docx** and study how Chapters 5 and 6 look (these are "Depth" chapters and are the template you must match). Pay extremely close attention to:
   - How headings look (colors, sizes, borders, spacing)
   - How "Also Known As" lists look (each alias on its own line)
   - How code blocks look (background shading, borders, font)
   - How tables look (header row styling, cell formatting)
   - How body text looks (font, size, line spacing)
   - How "Do's and Don'ts" sections look
   - How "The DC-Copilot Connection" sections look
   - How the cover page lists chapters (circled numbers ①②③④⑤⑥)
   - How the Table of Contents table works (Table 0 in the document)

2. **Delete ALL existing Chapter 7 content** from the docx (everything from "CHAPTER 7:" heading through the "Glossary Additions for Chapter 7" block). Leave the "Glossary Additions for Chapters 5 and 6" intact.

3. **Re-insert Chapter 7** from the markdown file, formatting every element to be visually identical to Chapter 6. The approach that WORKS is:
   - **Do NOT use python-docx programmatic styling** — it creates inline overrides that don't match the document's style sheet.
   - **Instead, use pandoc** to convert the Chapter 7 markdown to docx using the existing minibook docx as a `--reference-doc`, OR
   - **Clone actual XML elements** from Chapter 6 paragraphs (deep copy the lxml element, replace only the text content), OR
   - **Manually create a separate Ch7.docx** from the markdown with pandoc, style it in the same reference doc, then merge the body into the main file.
   - Whatever approach you choose, **visually verify** by comparing the XML of a Ch6 paragraph vs your Ch7 paragraph — they should be structurally identical.

4. **Update these parts of the docx:**
   - **Cover page**: Add `⑦ Prompt Engine Security & Defence — 17 defence techniques` (clone the ⑥ entry's exact XML, change the text)
   - **Cover page topic tags**: Add "Prompt Security" to the tag line
   - **TOC table** (Table 0, currently has rows for Ch1–Ch6): Add 18 rows for Ch7 (chapter header + 7.1–7.17)
   - **End-of-book note**: Should mention Chapter 7 (may already be done)

## FORMATTING SPEC FROM CHAPTERS 1–6 (discovered via python-docx inspection)

### Color Scheme
| Color   | Hex     | Used For |
|---------|---------|----------|
| Navy    | 1B3A5C  | Chapter headings (H1), main title |
| Blue    | 2E86AB  | Section headings (H2), cover features, bottom borders |
| Orange  | E8633B  | Sub-headings (H3) like "The Layman Explanation" |
| Dark    | 2C2C2C  | All body text |
| Gray    | 555555  | Secondary descriptive text |
| White   | FFFFFF  | Table header text |
| LightBG | F4F4F8  | Code block background (some blocks) |
| Border  | CCCCCC  | Code block left border |

### Paragraph Styles (from document style sheet)
| Style Name     | Font           | Size (half-pts) | Color  | Bold | Borders |
|---------------|----------------|-----------------|--------|------|---------|
| Heading 1     | Calibri Light  | 52 (26pt)       | 1B3A5C | Yes  | bottom: 1B3A5C, sz=12 |
| Heading 2     | Calibri Light  | 36 (18pt)       | 2E86AB | Yes  | bottom: 2E86AB, sz=6 |
| Heading 3     | Calibri Light  | 28 (14pt)       | E8633B | Yes  | none |
| First Paragraph | Calibri      | 21 (10.5pt)     | 2C2C2C | No   | none |
| Body Text     | Calibri        | 21 (10.5pt)     | 2C2C2C | First run bold | none |
| Compact       | Calibri        | 21 (10.5pt)     | 2C2C2C | No   | none (tight spacing) |
| Source Code   | Consolas       | 17 (8.5pt)      | 2C2C2C | No   | left: CCCCCC, sz=8 |
| Block Text    | Calibri        | 20 (10pt)       | 555555 | Yes  | background: F0F4F8 |
| Normal        | Calibri        | 20 (10pt)       | 2C2C2C | No   | none (used for empty separators) |

### Cover Page Feature Entry (paragraphs 3–8, reverse-ordered ⑥⑤④③②①)
Each entry has 3 runs in one paragraph:
- Run 1: `"  ⑥  "` — Calibri 13pt, color 2E86AB
- Run 2: `"Chapter Title"` — Calibri 12pt, color 1B3A5C, bold
- Run 3: `"  — description"` — Calibri 10pt, color 555555

### TOC Table (Table index 0)
- 4 columns: `#`, `Chapter`, `Depth`, `Page`
- Header row: bold white text (FFFFFF)
- Chapter rows: bold text (e.g., `7 | Prompt Engine Security... | Depth | Ch.7`)
- Section rows: normal text (e.g., `7.1 | Why Prompt Security... | | `)

### Section Structure (each section 7.x follows this pattern)
```
[empty Normal paragraph — separator]
[Heading 2] 7.x Section Title
[Heading 3] Also Known As
[Compact] alias 1          ← one per line, NOT bullet points
[Compact] alias 2
[Compact] alias 3
[Heading 3] The Layman Explanation
[First Paragraph] paragraph 1...
[First Paragraph] paragraph 2...
[Heading 3] Technical Sub-heading
[Source Code] code block content...
[Heading 3] Another Technical Sub-heading
[Source Code] more code...
[First Paragraph] body text...
[Table] comparison table
[Heading 3] The DC-Copilot Connection
[Source Code] DC-Copilot specific code/config...
[Heading 3] Do's and Don'ts
[Source Code] DO's / DON'Ts list with ✓ and ✗...
[empty Normal paragraph — separator before next section]
```

### Tables in the Body
- Use the "Table" style (the only table style in this doc)
- Header row: bold white text on dark background
- Data rows: regular dark gray text
- Cell font: Calibri ~9.5pt

## IMPORTANT NOTES

- The markdown has **bold markers** (`**text**`) in paragraphs — these should render as bold runs in the docx.
- "Also Known As" items in the markdown are `- item1\n- item2\n- item3` — each should be a separate Compact-styled paragraph, NOT a bulleted list, NOT joined on one line.
- Code blocks (``` ... ```) should use Source Code style with left border.
- The markdown has ASCII diagrams inside code blocks — preserve them exactly (they look great in Consolas).
- The Do's and Don'ts sections use ✓ and ✗ symbols inside code blocks.
- After Chapter 7 content, there's a **Glossary Additions for Chapter 7** block with ~20 term definitions. Each is `**Term** (aliases) — definition. [Section 7.x]`. These go before the existing "Glossary Additions for Chapters 5 and 6" block. Use Body Text style (bold term, regular description).

## VERIFICATION CHECKLIST
After completing, verify ALL of these:
- [ ] Chapter 7 heading looks identical to Chapter 6 heading (same color, size, border)
- [ ] Section headings (7.1–7.17) look identical to 6.1–6.12 headings
- [ ] Sub-headings (orange) look identical
- [ ] "Also Known As" aliases are separate lines, same style as Ch6 aliases
- [ ] Code blocks have the same left border, font, and spacing as Ch6 code blocks
- [ ] Tables have dark header rows with white text
- [ ] Body text font/size/color matches Ch6
- [ ] Cover page shows ⑦ entry above ⑥
- [ ] TOC table has 18 new rows for Chapter 7
- [ ] Chapter 7 glossary appears before Ch5/6 glossary
- [ ] End-of-book note mentions Chapter 7
- [ ] Open the docx in Word/Pages and visually scroll through Ch6 then Ch7 — they should look like siblings
