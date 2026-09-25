Title: "Flickr badge" que valida contra W3C
Date: 2006-11-03 00:07:17
Slug: flickr-badge-que-valida-contra-w3c
Tags: Howto, WordPress
Original_url: https://davidarcos.net/blog/2006/11/03/flickr-badge-que-valida-contra-w3c/

Quería poner un <span class="dead-link" title="Enlace roto: http://www.flickr.com/badge_new.gne">flickr badge</span> en la columna lateral derecha, pero me encontraba con que el código está lleno de errores y no hay manera de que [valide](http://validator.w3.org).

Al final me puse manos a la obra, hasta que lo he conseguido. Son tres simples pasos: obtener el script, modificar el HTML, y modificar el CSS. Me he basado en la idea de <span class="dead-link" title="Enlace roto: http://veerle.duoh.com/blog/comments/fickr_badge_w3c_valid/">este post</span> (en inglés). Así que aprovechamos el *script* de flickr (desechamos las tablas y demás basura) y le ponemos un CSS bonito:

1. Generamos un <span class="dead-link" title="Enlace roto: http://www.flickr.com/badge_new.gne">flickr badge</span> con nuestras preferencias.  
Del bloque de código que nos ofrece, sólo nos quedamos con la línea del script. Lo demás es basura: tablas anidadas, CSS empotrado, tags mal cerrados... puajj puajj, porquerías que hacen saltar varios errores contra el [validador del W3C](https://validator.w3.org/).  
La línea del script también es inválida, ya que usa <code>"&amp;"</code> donde tiene que usar <code>"&amp;"</code>. Así que sustituimos cada *&amp;* por *&amp;*  
<code>&lt;script type="text/javascript" xsrc="https://www.flickr.com/badge_code_v2.gne?show_name=1&amp;count=6&amp;display=random&amp;size=s&amp;layout=v&amp;source=user&amp;user=XXX&amp;"&gt;<br> &lt;/script&gt;</code>  
(donde XXX son distintas opciones;)
1. Incluimos este fragmento en nuestro código HTML. Yo lo he puesto en la columna de la derecha (sidebar.php):  
<code>&lt;div id="flickr"&gt;<br> &lt;script type="text/javascript" xsrc="https://www.flickr.com/badge_code_v2.gne?show_name=1&amp;count=6&amp;display=random&amp;size=s&amp;layout=v&amp;source=user&amp;user=XXX&amp;"&gt;<br> &lt;/script&gt;<br> &lt;/div&gt;</code>  
(con eso saldrían mis fotos. Para que salgan las tuyas, usa la línea del "script" que he nombrado antes que has generado desde <span class="dead-link" title="Enlace roto: http://www.flickr.com/badge_new.gne">flickr badge</span>)
1. Y también le metemos mano al CSS. He añadido:  
<code>#flickr {<br> width:200px;<br> height:250px;<br> padding:5px 0 0 50px;<br> }</code>  
<code>#flickr img {<br> float:left;<br> margin:0 0px 8px 8px;<br> background:#888;<br> padding:1px;<br> width:75px;<br> height:75px;<br> }</code>  
(aquí puedes personalizar bordes, colores, distancias, tamaños, etc..., para adaptarlo a la apariencia de tu blog)
1. Profit!

Con esto conseguimos un bonito *badge* con unas nuestras fotos de flickr, elegidas al azar. Y lo más importante, que **valida contra el W3C**, por lo que el blog seguirá siendo *accesible* y no sufrirá penalizaciones en los buscadores.

A disfrutar 🙂
