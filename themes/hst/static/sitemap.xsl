<?xml version="1.0" encoding="utf-8"?>
<!-- The sitemap, for a browser: a reader that lands on /sitemap.xml sees a page, not raw XML. Search engines ignore this. -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:sm="http://www.sitemaps.org/schemas/sitemap/0.9" exclude-result-prefixes="sm">
  <xsl:output method="html" encoding="utf-8" indent="yes"/>
  <xsl:template match="/">
    <html lang="es">
      <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title>Sitemap de David Arcos</title>
        <link rel="stylesheet" href="/theme/css/style.css"/>
      </head>
      <body>
        <main class="site-main">
          <h1 class="page-title">Sitemap de David Arcos</h1>
          <p>Esta dirección es un <strong>sitemap</strong>: la lista de las <xsl:value-of select="count(/sm:urlset/sm:url)"/> páginas del sitio, para los buscadores.<br/>Si buscas algo para leer, el mapa para personas está en <a href="/sobre-el-blog/#mapa">Sobre el blog</a>.</p>
          <ul>
            <xsl:for-each select="/sm:urlset/sm:url">
              <li><xsl:if test="sm:lastmod"><span class="yr"><xsl:value-of select="sm:lastmod"/></span>: </xsl:if><a href="{sm:loc}"><xsl:choose><xsl:when test="contains(sm:loc, '://')"><xsl:value-of select="concat('/', substring-after(substring-after(sm:loc, '://'), '/'))"/></xsl:when><xsl:otherwise><xsl:value-of select="sm:loc"/></xsl:otherwise></xsl:choose></a></li>
            </xsl:for-each>
          </ul>
          <p>Volver al <a href="/">inicio</a>.</p>
        </main>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
