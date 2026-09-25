<?xml version="1.0" encoding="utf-8"?>
<!-- The feed, for a browser: a reader that lands on /blog/feed.xml sees a page, not raw XML. Feed readers ignore this. -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:atom="http://www.w3.org/2005/Atom" exclude-result-prefixes="atom">
  <xsl:output method="html" encoding="utf-8" indent="yes"/>
  <xsl:template match="/">
    <html lang="es">
      <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title>Feed de <xsl:value-of select="/atom:feed/atom:title"/></title>
        <link rel="stylesheet" href="/theme/css/style.css"/>
      </head>
      <body>
        <main class="site-main">
          <h1 class="page-title">Feed de <xsl:value-of select="/atom:feed/atom:title"/></h1>
          <p>Esta dirección es un <strong>feed</strong>: pégala en tu lector de noticias y te avisará cuando haya una entrada nueva.</p>
          <ul>
            <xsl:for-each select="/atom:feed/atom:entry">
              <li><span class="yr"><xsl:value-of select="substring(atom:published, 1, 10)"/></span>: <a href="{atom:link[@rel='alternate']/@href}"><xsl:value-of select="atom:title"/></a></li>
            </xsl:for-each>
          </ul>
          <p>Volver al <a href="/blog/">blog</a>.</p>
        </main>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
