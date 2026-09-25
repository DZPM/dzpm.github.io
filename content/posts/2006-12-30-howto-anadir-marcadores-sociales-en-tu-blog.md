Title: HOWTO Añadir marcadores sociales en tu blog
Date: 2006-12-30 18:00:38
Slug: howto-anadir-marcadores-sociales-en-tu-blog
Tags: Howto, WordPress
Original_url: https://davidarcos.net/blog/2006/12/30/howto-anadir-marcadores-sociales-en-tu-blog/

Versión *corta*: he traducido y adaptado "Share This 1.3.1". Podéis descargar la versión en español: share-this-ES.zip *(ya no disponible)*

Versión *larga*:

Están de moda las **"webs sociales 2.0**". Desde luego son de utilidad, permiten tanto guardar y publicar tus enlaces favoritos en internet, sin depender de un disco duro (del.icio.us, technorati) como promocionar y compartir noticias (digg, meneame).

Existen multitud de plugins para WordPress que permiten enviar los artículos de un blog a alguno de estos sitios. El inconveniente que les he encontrado es que necesitas un icono para cada sitio, así que si pones unos cuandos (que se repiten por cada noticia), tu blog queda decorado como un arbolito de navidad. Por lo tanto, no me había decidido a usar ninguno.

Hace pocos días [apareció un nuevo plugin](http://alexking.org/blog/2006/12/12/share-this-13): **[Share This](http://alexking.org/projects/wordpress)**. La diferencia con los demás radica en que se trata de un solo icono (), y haciendo click en él puedes elegir entre varios marcadores sociales, o bien enviar dicho post por email. Me he decidido, y lo he instalado.  
No todo eran ventajas, le he encontrado algunos serios **inconvenientes**:

- Está sin traducir (sólamente en inglés) y sin adaptar (muchas webs sociales utilizadas en los EEUU, pero no en España, y viceversa).
- Utiliza codificación *ISO-8859-1* en vez de *UTF-8*. Si escribes en inglés, de acuerdo, pero si usad alfabetos internacionales...
- Aparece el icono junto a un texto (" *Share This*"), cuando yo solamente quiero el icono.
- Abusa de los scripts. Carga varios scripts innecesarios.
- Por defecto, abre un "*pop-up*" en AJAX. También puede abrir una página nueva, de manera que es mucho más *usable* (mucho más espacio, hay explicaciones, etc).
- Se incrusta donde él quiere, en el blog. Dependiendo del tema que uses, queda descolocado.
- Se incrusta incluso en los RSS ¬¬

Así que le he metido mano al código original, y he corregido los problemas anteriores: ahora está traducido, con webs sociales en castellano, y con el resto de *molestias* desactivadas o corregidas. Lo podéis descargar de aquí: share-this-ES.zip  
Las instrucciones de instalación son muy sencillas:

1. Descargar y descomprimir el archivo.
1. Guardar el directorio "share-this" en el "wp-content/plugins/" de tu blog.
1. Activar el plugin desde el panel de control del blog.
1. Añadir "<code><code>&lt;?php akst_share_link(); ?</code><code>&gt;</code></code>" en el código de nuestro blog. También se hace desde el panel de control, "Editor de temas". Añádelo donde quieras que aparezca el icono. Yo lo quiero en la página principal y en la de cada post *(index.php* y *single.php)*, y prefiero ponerlo al final del post (el lector querrá guardar el enlace después de leer el artículo, ¿no crees?)

De esta manera obtendremos el icono verde. El lector, al pulsar, será dirigido a una página done se le explica para qué sirve eso, y desde donde podrá **guardar** nuestro enlace, o bien **enviarlo** por email.
