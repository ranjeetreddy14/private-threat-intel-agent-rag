from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup

class WebSearch:
    def __init__(self):
        self.ddgs = DDGS()

    def search(self, query, max_results=3):
        """
        Performs a web search, fetches page content, and returns formatted results.
        """
        try:
            results = self.ddgs.text(query, max_results=max_results)
            formatted_results = []
            
            for r in results:
                title = r['title']
                url = r['href']
                snippet = r['body']
                
                # Try to fetch full page content
                page_content = self._fetch_page_content(url)
                
                if page_content:
                    formatted_results.append(
                        f"📄 {title}\n"
                        f"🔗 {url}\n"
                        f"📝 Content:\n{page_content[:1500]}...\n"  # Limit to 1500 chars per page
                    )
                else:
                    # Fallback to snippet if page fetch fails
                    formatted_results.append(
                        f"📄 {title}\n"
                        f"🔗 {url}\n"
                        f"📝 Snippet: {snippet}\n"
                    )
            
            return "\n\n".join(formatted_results)
        except Exception as e:
            return f"Search failed: {e}"

    def _fetch_page_content(self, url):
        """
        Fetches and extracts main text content from a URL.
        """
        try:
            # Set timeout and user agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = '\n'.join(lines)
            
            return text
        except Exception as e:
            print(f"[DEBUG] Failed to fetch {url}: {e}")
            return None
