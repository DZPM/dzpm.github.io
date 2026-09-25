Title: Cómo arreglar el plugin "Flickr Photo Album"
Date: 2006-09-13 14:48:25
Slug: como-arreglar-el-plugin-flickr-photo-album
Tags: Howto, WordPress
Original_url: https://davidarcos.net/blog/2006/09/13/como-arreglar-el-plugin-flickr-photo-album/

El plugin "Flickr Photo Album" (el que permite integrar las fotos de Flickr dentro de WordPress) ha tenido un problema, según leo en [tantannoodles](https://tantannoodles.com/toolkit/photo-album/):

> Important (Sept 12, 2006): The Flickr API key this plugin uses has apparently exceeded it's usage limits. YOU WILL need to follow the instructions [outlined in this thread](https://www.flickr.com/groups/tantannoodles/discuss/72157594279842288/) in order to get this plugin to work. I will try to have a better solution for the next release.

Sé que varios de vosotros usáis este plugin, así que os explico como solucionarlo.  
  
El problema es que la clave para la API que usa esta extensión ha excedido el uso máximo permitido: vamos, que ha muerto de éxito. La solución consiste en hacernos una clave API para nosotros.

- Nos hacemos una clave API en [https://www.flickr.com/services/api/key.gne](https://www.flickr.com/services/api/key.gne)  
Una vez creada, vamos a la configuración y le ponemos **el nombre de nuestro blog**, y le cambiamos el tipo de autentificación a **Desktop Application**
- Después, editamos plugins/silaspartners/flickr/lib.flickr.php.  
Tenemos un trozo así (las claves API me las he inventado):  
<code>// keys<br> define("SILAS_FLICKR_APIKEY", "1111111111111111");<br> define("SILAS_FLICKR_SHAREDSECRET", "222222222222");</code>  
Basta con cambiar esos números por las claves que nos ha dado flickr.
- Finalmente volvemos a las opciones de nuestro blog, y entramos en la configuración del plugin.

Problema complicado, solucion sencilla. El fallo salió ayer, y hoy ya está corregido: viva el software libre.  
Y ya podemos seguir usando el plugin otra ves 🙂
