# Cemaco Website Analysis

## URL Structure
- Main site: https://www.cemaco.com/
- Search URL pattern: https://www.cemaco.com/#b097/fullscreen/m=and&q=iPhone

## Search Results Found
Successfully found 55 iPhone-related products including:

1. **Igel Audífonos Alámbricos para iPhone** - Q54.99
2. **Apple iPhone 16e de 128Gb Blanco** - Q6,499.00
3. **Apple iPhone 16e Negro 128 GB** - Q6,499.00
4. **Base Cargador Conector iPhone** - Q69.99
5. **Apple iPhone 13 128 Gb Azul Medianoche** - Q4,299.00

## Key Observations

### Website Structure
- Uses a hash-based routing system (#b097/fullscreen/...)
- Search results are dynamically loaded
- Products display with clear pricing in Quetzales (Q)
- Each product has an "AGREGAR" (Add) button

### Product Information Available
- Product names
- Prices in GTQ (Quetzales)
- Brand information (Apple, Igel)
- Product images
- Stock status ("24 horas dentro de la capital")

### Technical Details
- The site appears to use JavaScript for search functionality
- Search results are loaded dynamically, not through traditional form submission
- URL contains search parameters in hash fragment

## Issues with Current Scraper
1. **Wrong URL Pattern**: Current scraper uses `/search?q=` but Cemaco uses hash-based routing
2. **Dynamic Content**: Content is loaded via JavaScript, not static HTML
3. **Headers**: May need specific headers to avoid blocking

## Recommended Fixes
1. Update search URL pattern to use hash-based routing
2. Add JavaScript rendering capability or use Playwright
3. Update CSS selectors based on actual HTML structure
4. Add proper headers and user agent strings

