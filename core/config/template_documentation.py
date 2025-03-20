from typing import Dict, Any, Optional
from datetime import datetime
import json
import re
from pathlib import Path
import markdown
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader

from app.core.models.template import RecoveryTemplate, ValidationRule
from app.core.schemas.template import TemplateResponse

class TemplateDocumentationService:
    """Service for generating template documentation."""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates" / "documentation"
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # Load translations
        self.translations = {
            'en': self._load_translations('en'),
            'fa': self._load_translations('fa')
        }
    
    def _load_translations(self, language: str) -> Dict[str, str]:
        """Load translations for a specific language."""
        translation_file = self.template_dir / "translations" / f"{language}.json"
        if translation_file.exists():
            with open(translation_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _translate(self, key: str, language: str) -> str:
        """Translate a key to the specified language."""
        return self.translations.get(language, {}).get(key, key)
    
    def _generate_markdown(self, template: RecoveryTemplate, language: str) -> str:
        """Generate markdown documentation for a template."""
        template = self.env.get_template('template.md')
        return template.render(
            template=template,
            translate=lambda k: self._translate(k, language),
            validation_rules=template.validation_rules,
            parameters=template.parameters,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
    
    def _generate_pdf(self, template: RecoveryTemplate, language: str) -> bytes:
        """Generate PDF documentation for a template."""
        # First generate markdown
        markdown_content = self._generate_markdown(template, language)
        
        # Convert markdown to HTML
        html_content = markdown.markdown(markdown_content)
        
        # Apply HTML template
        html_template = self.env.get_template('template.html')
        full_html = html_template.render(
            content=html_content,
            template=template,
            translate=lambda k: self._translate(k, language),
            language=language
        )
        
        # Convert HTML to PDF
        return HTML(string=full_html).write_pdf()
    
    def generate_documentation(
        self,
        template: RecoveryTemplate,
        format: str = 'markdown',
        language: str = 'en'
    ) -> Any:
        """Generate documentation for a template in the specified format and language."""
        if format == 'markdown':
            return self._generate_markdown(template, language)
        elif format == 'pdf':
            return self._generate_pdf(template, language)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_documentation_filename(
        self,
        template: RecoveryTemplate,
        format: str
    ) -> str:
        """Generate a filename for the documentation."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"template_{template.id}_{template.name}_{timestamp}.{format}" 