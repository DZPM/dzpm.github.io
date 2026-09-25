Title: Sobre el blog
Slug: sobre-el-blog
Template: sobre
Summary: Cuándo se creó este blog, por dónde ha pasado, cómo funciona ahora, y el mapa del sitio.

**Hic sunt trolls** nace en julio de 2006, antes de [un Erasmus en Bergen](/blog/por-que-este-blog/) (Noruega).  
En los mapas antiguos, donde se acaba lo conocido, ponían <span class="motto">hic sunt dracones</span>. En Noruega hay trolls.  
El blog empezó como un diario, y acabó guardando charlas.

## Cronología

<div class="timeline history" markdown="1">
<div class="year-row" markdown="1">
<div class="year-big">2006</div>
<div class="year-note" markdown="1">
El 5 de julio, [fr1st p0st](/blog/fr1st-p0st/): WordPress en el servidor de [l'Oasi](/blog/etiquetas/loasi/), en la UPC, un Debian. En diciembre, [primer cambio de hosting](/blog/cambio-de-hosting/): un DreamHost entre 5 amigos.
</div>
</div>
<div class="year-row" markdown="1">
<div class="year-big">2007</div>
<div class="year-note" markdown="1">
[Un año de vida](/blog/aniversario-de-hic-sunt-trolls/): más de 100 entradas, 400 comentarios y 8 portadas en menéame. [Una actualización forzada](/blog/algo-ha-cascau-riau-riau/) rompe medio blog; [una brecha en DreamHost](/blog/hackeado-blog-brecha-seguridad-dreamhost/) lo llena de spam.
</div>
</div>
<div class="year-row" markdown="1">
<div class="year-big">2009</div>
<div class="year-note" markdown="1">
[Nueva migración](/blog/migracion-del-blog/): de DreamHost a un servidor propio, del directorio raíz a `/blog/`, y llegan las etiquetas y los widgets.
</div>
</div>
<div class="year-row" markdown="1">
<div class="year-big">2013</div>
<div class="year-note" markdown="1">
El blog se muda a un VPS de DigitalOcean con Ubuntu, que sobrevivió hasta 2026.
</div>
</div>
<div class="year-row" markdown="1">
<div class="year-big">2016</div>
<div class="year-note" markdown="1">
[Diez años](/blog/diez-anos-de-hic-sunt-trolls/) desde el primer post. Rompía una lanza a favor de mantener un WordPress propio; la mantuve otros diez años.
</div>
</div>
<div class="year-row" markdown="1">
<div class="year-big">2018</div>
<div class="year-note" markdown="1">
Un DDoS puntual me lleva a poner el blog detrás de [Cloudflare](https://www.cloudflare.com/).
</div>
</div>
<div class="year-row" markdown="1">
<div class="year-big">2026</div>
<div class="year-note" markdown="1">
**[Veinte años](/blog/veinte-anos-de-hic-sunt-trolls/).** El blog pasa a ser un sitio estático: **133** entradas migradas de WordPress (más una recuperada de 2006 y las nuevas), **463** comentarios, **575** redirecciones y **182** enlaces muertos limpiados. El cómo, en [el repositorio](https://github.com/DZPM/dzpm.github.io).
</div>
</div>
</div>

## Cifras

Las cuenta el build, cada vez, a partir del contenido.

- **{{ stats.posts }}** entradas desde {{ stats.first_year }}: **{{ stats.archive }}** de la etapa personal (hasta 2009) y **{{ stats.portfolio }}** de charlas y artículos (desde 2012).
- **{{ stats.words }}** palabras en las entradas, **{{ stats.comment_words }}** más en los comentarios y **{{ stats.mention_words }}** en las menciones: la conversación es la mitad del blog.
- **{{ stats.comments }}** comentarios, entre {{ stats.comments_from }} y {{ stats.comments_to }}, de **{{ stats.people }}** personas distintas. ¡Gracias!
- **{{ stats.mentions }}** menciones de otros blogs (pingbacks y trackbacks), de las que **{{ stats.dead_mentions }}** ya no responden.
- **{{ stats.tags }}** [etiquetas](/blog/etiquetas/).
- **{{ stats.photos }}** fotos recuperadas en **{{ stats.photo_posts }}** entradas, **{{ stats.covers }}** covers y **{{ stats.embeds }}** vídeos, presentaciones y audios incrustados.
- **{{ stats.external }}** enlaces a otros sitios; **{{ stats.dead }}** de ellos ya no llevan a ninguna parte y se muestran como texto.
- **{{ stats.meneame_posts }}** entradas llegaron a la portada de menéame, con **{{ stats.meneos }}** meneos en total.
- **{{ stats.stubs }}** redirecciones desde las direcciones antiguas de WordPress.

## Cómo funciona ahora

- [Código libre](https://github.com/DZPM/dzpm.github.io) (GPL-3.0); textos e imágenes, CC BY-SA 4.0.
- Sin JavaScript, salvo el selector de tema y el buscador.
- Los textos los escribo yo; la migración de 2026, con ayuda de Claude Code.
- Sin comentarios nuevos ni analítica: los enlaces de abajo son el contacto.
- Un comentario tuyo que quieras borrar: pídelo ([issue](https://github.com/DZPM/dzpm.github.io/issues), LinkedIn o X) y lo quito.
