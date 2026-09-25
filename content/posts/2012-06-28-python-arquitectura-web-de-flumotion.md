Title: Python y la Arquitectura web de Flumotion
Date: 2012-06-28 15:21:39
Slug: python-arquitectura-web-de-flumotion
Tags: Django, Flumotion, Python, Software Libre
Summary: Los servicios web de Flumotion, casi todos en Python: del CMS y el portal de cliente a los servidores.
Kind: artículo
Cover: python-arquitectura-web-de-flumotion.jpg
Original_url: https://davidarcos.net/blog/2012/06/28/python-arquitectura-web-de-flumotion/

De vez en cuando hay gente que me pregunta por la **arquitectura de los servicios web de [Flumotion](/blog/etiquetas/flumotion/)**. En este artículo voy a tratar de hacer una breve explicación técnica, empezando con los **servicios** web principales y acabando con los **servidores**.

## Servicios:

En primer lugar hay que destacar que casi todo en Flumotion está hecho en [Python](https://python.org/), así que la elección para los servicios web era fácil. A las ventajas intrínsecas de Python (mantenibilidad del código, desarrollo rápido, gran cantidad de librerías, *menos magia*, etc) se le une la facilidad de integración con el resto de los componentes de la plataforma.

- [**Flumotion.com**](https://www.flumotion.com) es el típico web corporativo. Es un CMS multi-idioma, con algo de lógica específica. Utiliza [DjangoCMS](https://www.django-cms.org) y un par de apps Django a medida.

- **<span class="dead-link" title="Enlace roto: https://mediaconsole.flumotion.com">Flumotion MediaConsole</span>** es el portal de cliente desde donde los usuarios pueden previsualizar contenidos, parar/arrancar flujos y componentes, gestionar la publicidad, alertas, seguridad (IPs autorizadas, tokens), etc. Destaca la sección de estadísticas, con todo tipo de métricas, filtros y consultas.

    Los retos principales eran la complejidad de la gran cantidad de *features*, garantizar la *accountability* (saber en todo momento quien ha ejecutado qué, detectar los errores antes que el cliente, etc), y la importación automatizada de todo tipo de datos (de bases de datos y ficheros de configuración existentes).

    Es un típico proyecto [Django](https://www.djangoproject.com/), con unas 15-20 aplicaciones bastante independientes entre sí. Utiliza su propia base de datos MySQL, aunque también accede a varias bases de datos externas. Para la importación, muchas [fixtures](https://docs.djangoproject.com/en/dev/howto/initial-data/#providing-initial-data-with-fixtures). A destacar: se implementó hace tres años (2009), cuando no existían el [multidatabase de Django 1.2](https://docs.djangoproject.com/en/stable/topics/db/multi-db/), ni [South](https://south.aeracode.org/), ni [Sentry](https://docs.sentry.io/) ni todas esas cosas que hoy en día facilitan tanto la vida 😉

- **Enthalpy** se encarga de consolidar los logs de las sesiones de la plataforma y generar las estadísticas.

    El primer reto era hacer un sistema escalable y distribuido, ya que su antecesor era centralizado - y se quedó corto: en ocasiones tardaba más de una hora en consolidar una hora de datos. El segundo reto era optimizar el espacio en disco: estamos hablando de una base de datos que crecía 300-400 GB al mes (truco: guardarlo en formato [ARCHIVE](https://dev.mysql.com/doc/refman/5.1/en/archive-storage-engine.html) te ahorra un orden de magnitud).

    Está implementado en [Twisted](https://twisted.org/) (Python asíncrono), utiliza MySQL con [SQLAlchemy](https://www.sqlalchemy.org/) (excepto para las queries más pesadas, implementadas directamente en SQL). Ahora mismo se ejecuta en cuatro máquinas, que suman varios teras de datos consolidados.

- <span class="dead-link" title="Enlace roto: https://backoffice.flumotion.com">**Flumotion Backoffice**</span> es el portal de administración interna. Se usa para integrar y configurar los servicios de la plataforma de streaming. Utiliza Django y [SQLAlchemy](https://www.sqlalchemy.org/) y está integrado con los servicios internos: LDAP, bases de datos, plataforma.

- <span class="dead-link" title="Enlace roto: https://manager.livetranscoding.com">**Livetranscoding Manager**</span> es (era) el portal de cliente de [Livetranscoding.com](https://web.archive.org/web/20120628054947/http://www.livetranscoding.com/). Desde allí el cliente podía comprar servicios (streams), inicializarlos (se arrancaban las máquinas en la nube, en tiempo real), previsualizarlos y configurarlos. Livetranscoding soportaba muchísimos formatos (a varias resoluciones, multi-bitrate...), y permitía elegir el CDN de salida.

    Utiliza Django con Twisted, MySQL, South, y [Fabric](https://docs.fabfile.org/). Como todo tiene que ser asíncrono y a tiempo real, utiliza un sistema de colas ([RabbitMQ](https://www.rabbitmq.com/)) y, para comunicarse con el navegador, [websockets](https://websockets.spec.whatwg.org/).

- **Flumotion WebTV** (también conocido como [Online Video Platform](https://web.archive.org/web/20120621035616/http://www.flumotion.com/en/services/video-platform/)) es la plataforma de TV y radio online.

    Desde el punto de vista técnico, imagínate un clon de Youtube... pero con muchísimas más *features*, muchas opciones para gestionar la publicidad, mucha flexibilidad (cada cliente lo quiere *un poco distinto*), y una API potente que haga todo eso.

    Utiliza Django, MySQL, South, Fabric, [Celery](https://docs.celeryq.dev/), Sentry. Optimizaciones para escalabilidad web: memcache a varios niveles, servidores de estáticos a parte, balanceo de carga por DNS entre máquinas de un cluster (actualmente hay dos clústeres).

- **Flumotion WebTV Backoffice** es el portal desde donde el cliente gestiona su WebTV. Destaca entre las demás por que no está hecho en Python, sino en Flash (en el framework [Flex](https://flex.apache.org/)). Internamente hace llamadas a la API de WebTV.

## Servidores:

Para el hardware, usamos nuestra propia infraestructura. La plataforma de streaming está compuesta por varios cientos de máquinas, en centros de datos por ciudades de todo el mundo.

- El sistema operativo es Red Hat.
- Como servidor de aplicaciones usamos [Gunicorn](https://gunicorn.org/).
- Para controlar las instancias de Gunicorn, [Supervisord](https://supervisord.org/).
- Como servidor HTTP, [nginx](https://nginx.org/). Redirige al servidor de Gunicorn, y también lo usamos para servir los estáticos.
- Nota: anteriormente usábamos apache+mod_wsgi, era más difícil de configurar y menos eficiente que nginx+gunicorn.
- Se usa [virtualenv](https://virtualenv.pypa.io/) para gestionar la gran cantidad de servicios y versiones. De lo contrario, sería un caos de dependencias.
- Para el control de versiones, git (algún proyecto antiguo sigue en svn). No hacemos paquetes para web, sino que desplegamos directamente a partir de un tag o una rama.
- Para desplegar nuevas máquinas, o bien cambios de configuración, [Puppet](https://www.puppet.com/).
- Integración continua con [Buildbot](https://buildbot.net/).
- Todas las bases de datos son máquinas dedicadas con MySQL, y las más críticas están en réplica master-slave.
- Para la cache, memcached por todos los lados.
