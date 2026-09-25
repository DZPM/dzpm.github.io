Title: La plataforma de reconocimiento de imágenes de Catchoom
Date: 2013-05-23 10:08:40
Slug: plataforma-reconocimiento-imagenes-de-catchoom
Tags: Catchoom, Django, Image Recognition, Python, Slides, Video
Summary: Qué es el reconocimiento de imágenes y cómo funciona la plataforma de Catchoom, recién rediseñada.
Kind: charla
Cover: plataforma-reconocimiento-imagenes-de-catchoom.jpg
Original_url: https://davidarcos.net/blog/2013/05/23/plataforma-reconocimiento-imagenes-de-catchoom/

Durante los últimos meses he estado trabajando en el [Catchoom Recognition Service](https://catchoom.com/). Aprovechando que [acabamos de rediseñarlo por completo](https://web.archive.org/web/20130915022253/http://catchoom.com/blog/new-improved-web-panel-for-our-saas-platform-users/), voy a explicar un poco de qué va el proyecto. Antes de nada, **te invito a probarlo:**

1. Registra [una cuenta gratuita](https://web.archive.org/web/20130702231722/https://crs.catchoom.com/accounts/signup/), y probando la plataforma de **Image Recognition**:
![Botón de registro en el Catchoom Recognition Service]({static}/images/posts/catchoom_recognition_service-300x110.jpg)

1. Usa la **librería Python** ([catchoom-python](https://github.com/web1o1/catchoom-python)), para integrar las APIs. Aunque no uses Python (ehem, [empieza a usarlo](https://learnpythonthehardway.org/book/) 😉), puedes aprovechar las herramientas de subir/reconocer imágenes y las imágenes de ejemplo.
1. Visita la nueva [web Catchoom](https://catchoom.com/).

Agradeceré mucho las opiniones, críticas y sugerencias 🙂

## ¿Qué es el "Image Recognition"?

Básicamente, el reconocimiento de imágenes consiste en **enviar una foto** (por ejemplo, desde el móvil), **compararla** contra una base de datos de imágenes de referencia, **y reconocer** qué objeto aparece en esa foto.

A partir de ahí, los retos están en hacerlo lo más rápido posible (&lt;0.5s), mejorar la detección (varios objetos en la misma imagen, imágenes borrosas/distorsionadas, 3D...), asociar metadatos a cada objeto (cada cliente tiene necesidades distintas), ofrecer estadísticas de uso, y, en general, tener una plataforma segura, escalable y automatizada.

Vale, ¿y para qué sirve el reconocimiento de imagen? ¿Qué se puede hacer con esto? Pues lo que se te ocurra:

- integrarlo en aplicaciones móviles para reconocer logotipos o marcas comerciales
- añadirlo a un videojuego para reconocer objetos (y darte bonus dentro del juego)
- reconocer objetos para aplicar realidad aumentada encima, utilizarlo para reconocer cuadros, edificios, portadas de CDs, catálogos/revistas...
- o, mi uso favorito: sustituir (y enterrar) a los [códigos QR](https://picturesofpeoplescanningqrcodes.tumblr.com/) 😉

## Arquitectura de la plataforma de Catchoom

La plataforma está implementada en [Python](https://python.org/), los componentes usan [Django](https://www.djangoproject.com/), [Tornado](https://www.tornadoweb.org/) y [Gevent](https://www.gevent.org/). Toda la infrastructura está en [Amazon Web Services](https://aws.amazon.com/).

A destacar, usamos [Redis](https://redis.io/) para varios servicios. Expliqué las [ventajas de usar Redis](https://web.archive.org/web/20130530154803/http://2012.nosql-matters.org/bcn/speakers/) en el [NoSQL matters@Barcelona2012](https://web.archive.org/web/20130531054624/http://2012.nosql-matters.org/bcn/), el pasado Octubre, así que puedes ver <span class="dead-link" title="Enlace roto: https://vimeo.com/52213638">el vídeo</span>:

*(Aquí había <span class="dead-link" title="Enlace roto: https://vimeo.com/52213638">el vídeo de la charla</span>, en Vimeo. Ya no existe.)*

Y [la presentación](https://www.slideshare.net/DZPM/nosql-matters-in-catchoom-recognition-service-14631138): (inexplicablemente llegó a portada en Slideshare, de ahí las visitas)

https://www.slideshare.net/slideshow/embed_code/14631138

Gracias de antemano por probar [el reconocimiento de imagen de Catchoom](https://web.archive.org/web/20130702231722/https://crs.catchoom.com/accounts/signup/), espero tu feedback 😀
