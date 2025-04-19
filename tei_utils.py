import re
from lxml import etree

def convert_to_tei(title, author, year, text_content):
    """
    Convert plain text to basic TEI XML format
    """
    # Create the TEI structure
    tei = etree.Element("TEI", xmlns="http://www.tei-c.org/ns/1.0")
    
    # Create teiHeader
    tei_header = etree.SubElement(tei, "teiHeader")
    
    # Add fileDesc
    file_desc = etree.SubElement(tei_header, "fileDesc")
    
    # Add titleStmt
    title_stmt = etree.SubElement(file_desc, "titleStmt")
    title_elem = etree.SubElement(title_stmt, "title")
    title_elem.text = title
    
    author_elem = etree.SubElement(title_stmt, "author")
    author_elem.text = author
    
    # Add publicationStmt
    pub_stmt = etree.SubElement(file_desc, "publicationStmt")
    pub_year = etree.SubElement(pub_stmt, "date")
    pub_year.text = str(year)
    
    # Add sourceDesc
    source_desc = etree.SubElement(file_desc, "sourceDesc")
    p = etree.SubElement(source_desc, "p")
    p.text = "Converted to TEI by TATTVA project"
    
    # Create text element
    text_elem = etree.SubElement(tei, "text")
    body = etree.SubElement(text_elem, "body")
    
    # Process the text content - split by paragraphs
    paragraphs = text_content.split('\n\n')
    
    for para in paragraphs:
        if para.strip():
            p = etree.SubElement(body, "p")
            p.text = para.strip()
    
    # Return the TEI XML as a string
    return etree.tostring(tei, pretty_print=True, encoding='unicode')

def identify_entities(text):
    """
    Basic entity recognition for Sanskrit texts
    Returns text with potential entities marked
    """
    # This is a simplified example - in a real implementation,
    # you would use NLP or pattern matching specific to Sanskrit
    
    # Example: Mark potential person names (simplified)
    text = re.sub(r'\b([A-Z][a-z]+)\b', r'<persName>\1</persName>', text)
    
    # Example: Mark potential place names (simplified)
    place_patterns = ['kingdom of', 'city of', 'mountain of']
    for pattern in place_patterns:
        text = re.sub(f'{pattern} ([A-Z][a-z]+)', f'{pattern} <placeName>\\1</placeName>', text)
    
    return text