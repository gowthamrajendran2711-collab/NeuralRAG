"""Document parsers: PDF, DOCX, HTML, Markdown"""
import aiofiles
import httpx
from pathlib import Path

class DocumentParser:
    async def parse(self, source: str) -> str:
        if source.startswith("http://") or source.startswith("https://"):
            return await self._parse_url(source)
        return await self._parse_file(source)

    async def _parse_url(self, url: str) -> str:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            r = await client.get(url)
            r.raise_for_status()
            content_type = r.headers.get("content-type","")
            if "pdf" in content_type:
                return self._parse_pdf_bytes(r.content)
            return self._strip_html(r.text)

    async def _parse_file(self, path: str) -> str:
        p = Path(path)
        if p.suffix == ".pdf":
            import pypdf
            reader = pypdf.PdfReader(path)
            return "\n".join(page.extract_text() for page in reader.pages)
        elif p.suffix == ".docx":
            import docx
            doc = docx.Document(path)
            return "\n".join(para.text for para in doc.paragraphs)
        elif p.suffix in (".md", ".txt"):
            async with aiofiles.open(path) as f:
                return await f.read()
        raise ValueError(f"Unsupported file type: {p.suffix}")

    def _strip_html(self, html: str) -> str:
        import html2text
        return html2text.html2text(html)

    def _parse_pdf_bytes(self, data: bytes) -> str:
        import io, pypdf
        reader = pypdf.PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() for page in reader.pages)
