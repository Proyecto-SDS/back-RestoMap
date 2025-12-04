CREATE TABLE "Rol" (
  "id" integer PRIMARY KEY,
  "nombre" varchar(100) UNIQUE NOT NULL
);

CREATE TABLE "Comuna" (
  "id" integer PRIMARY KEY,
  "nombre" varchar(100) UNIQUE NOT NULL
);

CREATE TABLE "TipoLocal" (
  "id" integer PRIMARY KEY,
  "nombre" varchar(100) UNIQUE NOT NULL
);

CREATE TABLE "TipoRed" (
  "id" integer PRIMARY KEY,
  "nombre" varchar(100) UNIQUE NOT NULL
);

CREATE TABLE "TipoFoto" (
  "id" integer PRIMARY KEY,
  "nombre" varchar(100) UNIQUE NOT NULL
);

CREATE TABLE "Categoria" (
  "id" integer PRIMARY KEY,
  "nombre" varchar(100) UNIQUE NOT NULL
);

CREATE TABLE "Direccion" (
  "id" integer PRIMARY KEY,
  "id_comuna" integer,
  "calle" varchar(100) NOT NULL,
  "numero" integer NOT NULL,
  "longitud" decimal NOT NULL,
  "latitud" decimal NOT NULL
);

CREATE TABLE "Local" (
  "id" integer PRIMARY KEY,
  "id_direccion" integer NOT NULL,
  "id_tipo_local" integer NOT NULL,
  "descripcion" varchar(200) NOT NULL,
  "nombre" varchar(200) NOT NULL,
  "telefono" integer NOT NULL,
  "correo" varchar(50) UNIQUE NOT NULL
);

CREATE TABLE "Horario" (
  "id" integer PRIMARY KEY,
  "id_local" integer NOT NULL,
  "tipo" varchar(50) NOT NULL,
  "fecha_inicio" date NOT NULL,
  "fecha_fin" date NOT NULL,
  "dia_semana" smallint NOT NULL,
  "hora_apertura" time NOT NULL,
  "hora_cierre" time NOT NULL,
  "abierto" boolean NOT NULL DEFAULT true,
  "nota" varchar(500)
);

CREATE TABLE "Mesa" (
  "id" integer PRIMARY KEY,
  "id_local" integer NOT NULL,
  "nombre" varchar(30) NOT NULL,
  "descripcion" varchar(100),
  "capacidad" smallint NOT NULL,
  "estado" varchar(50) NOT NULL
);

CREATE TABLE "Usuario" (
  "id" integer PRIMARY KEY,
  "nombre" varchar(100) NOT NULL,
  "correo" varchar(100) UNIQUE NOT NULL,
  "contrasena" varchar(200) NOT NULL,
  "telefono" varchar(32),
  "id_rol" integer,
  "id_local" integer,
  "creado_el" timestamp NOT NULL
);

CREATE TABLE "Foto" (
  "id" integer PRIMARY KEY,
  "id_local" integer,
  "id_producto" integer,
  "id_categoria" integer,
  "id_tipo_foto" integer,
  "ruta" text NOT NULL
);

CREATE TABLE "Redes" (
  "id" integer PRIMARY KEY,
  "id_local" integer NOT NULL,
  "id_tipo_red" integer,
  "id_foto" integer,
  "nombre_usuario" varchar(255) NOT NULL,
  "url" text NOT NULL
);

CREATE TABLE "Producto" (
  "id" integer PRIMARY KEY,
  "id_local" integer NOT NULL,
  "id_categoria" integer,
  "nombre" varchar(100) NOT NULL,
  "descripcion" varchar(500),
  "estado" varchar(50) NOT NULL,
  "precio" integer NOT NULL
);

CREATE TABLE "Opinion" (
  "id" integer PRIMARY KEY,
  "id_usuario" integer NOT NULL,
  "id_local" integer NOT NULL,
  "puntuacion" numeric(2,1) NOT NULL,
  "comentario" varchar(500) NOT NULL,
  "creado_el" timestamp NOT NULL,
  "eliminado_el" timestamp
);

CREATE TABLE "Favorito" (
  "id" integer PRIMARY KEY,
  "id_usuario" integer NOT NULL,
  "id_local" integer NOT NULL,
  "agregado_el" timestamp NOT NULL
);

CREATE TABLE "Reserva" (
  "id" integer PRIMARY KEY,
  "id_local" integer NOT NULL,
  "id_usuario" integer NOT NULL,
  "fecha_reserva" date NOT NULL,
  "hora_reserva" time NOT NULL,
  "estado" varchar(50) NOT NULL,
  "creado_el" timestamp NOT NULL,
  "expirado_el" timestamp
);

CREATE TABLE "ReservaMesa" (
  "id" integer PRIMARY KEY,
  "id_reserva" integer NOT NULL,
  "id_mesa" integer NOT NULL,
  "prioridad" varchar(50) NOT NULL
);

CREATE TABLE "QRDinamico" (
  "id" integer PRIMARY KEY,
  "id_mesa" integer NOT NULL,
  "id_pedido" integer,
  "id_reserva" integer,
  "id_usuario" integer NOT NULL,
  "codigo" varchar(255) UNIQUE NOT NULL,
  "expiracion" timestamp NOT NULL,
  "activo" boolean NOT NULL DEFAULT true,
  "creado_el" timestamp NOT NULL
);

CREATE TABLE "Pedido" (
  "id" integer PRIMARY KEY,
  "id_local" integer NOT NULL,
  "id_mesa" integer NOT NULL,
  "id_usuario" integer NOT NULL,
  "id_qr" integer NOT NULL,
  "creado_por" integer NOT NULL,
  "estado" varchar(50) NOT NULL DEFAULT 'iniciado',
  "total" integer NOT NULL DEFAULT 0,
  "creado_el" timestamp NOT NULL,
  "actualizado_el" timestamp
);

CREATE TABLE "Cuenta" (
  "id" integer PRIMARY KEY,
  "id_pedido" integer NOT NULL,
  "id_producto" integer NOT NULL,
  "creado_por" integer NOT NULL,
  "cantidad" integer NOT NULL,
  "observaciones" varchar(500),
  "creado_el" timestamp NOT NULL
);

CREATE TABLE "EstadoPedido" (
  "id" integer PRIMARY KEY,
  "id_pedido" integer NOT NULL,
  "estado" varchar(50) NOT NULL,
  "creado_por" integer NOT NULL,
  "creado_el" timestamp NOT NULL,
  "nota" varchar(200)
);

CREATE TABLE "Encomienda" (
  "id" integer PRIMARY KEY,
  "id_pedido" integer NOT NULL,
  "estado" varchar(50) NOT NULL,
  "creado_el" timestamp NOT NULL
);

CREATE TABLE "EncomiendaCuenta" (
  "id" integer PRIMARY KEY,
  "id_cuenta" integer NOT NULL,
  "id_encomienda" integer NOT NULL
);

CREATE TABLE "Pago" (
  "id" integer PRIMARY KEY,
  "id_pedido" integer NOT NULL,
  "creado_por" integer NOT NULL,
  "metodo" varchar(50) NOT NULL,
  "estado" varchar(50) NOT NULL,
  "monto" integer NOT NULL,
  "creado_el" timestamp NOT NULL,
  "actualizado_el" timestamp
);

CREATE INDEX ON "Direccion" ("id_comuna");

CREATE INDEX ON "Local" ("id_direccion");

CREATE INDEX ON "Local" ("id_tipo_local");

CREATE INDEX ON "Local" ("correo");

CREATE INDEX ON "Horario" ("id_local");

CREATE INDEX ON "Mesa" ("id_local");

CREATE INDEX ON "Mesa" ("estado");

CREATE INDEX ON "Usuario" ("correo");

CREATE INDEX ON "Usuario" ("id_rol");

CREATE INDEX ON "Usuario" ("id_local");

CREATE INDEX ON "Usuario" ("creado_el");

CREATE INDEX ON "Foto" ("id_local");

CREATE INDEX ON "Foto" ("id_producto");

CREATE INDEX ON "Foto" ("id_categoria");

CREATE INDEX ON "Foto" ("id_tipo_foto");

CREATE INDEX ON "Redes" ("id_local");

CREATE INDEX ON "Redes" ("id_tipo_red");

CREATE INDEX ON "Redes" ("id_foto");

CREATE INDEX ON "Producto" ("id_local");

CREATE INDEX ON "Producto" ("id_categoria");

CREATE INDEX ON "Producto" ("estado");

CREATE INDEX ON "Opinion" ("id_usuario");

CREATE INDEX ON "Opinion" ("id_local");

CREATE INDEX ON "Opinion" ("creado_el");

CREATE UNIQUE INDEX ON "Favorito" ("id_usuario", "id_local");

CREATE INDEX ON "Favorito" ("agregado_el");

CREATE INDEX ON "Reserva" ("id_local");

CREATE INDEX ON "Reserva" ("id_usuario");

CREATE INDEX ON "Reserva" ("creado_el");

CREATE INDEX ON "Reserva" ("fecha_reserva");

CREATE UNIQUE INDEX ON "ReservaMesa" ("id_reserva", "id_mesa");

CREATE INDEX ON "QRDinamico" ("id_mesa");

CREATE INDEX ON "QRDinamico" ("id_pedido");

CREATE INDEX ON "QRDinamico" ("id_reserva");

CREATE INDEX ON "QRDinamico" ("id_usuario");

CREATE INDEX ON "QRDinamico" ("codigo");

CREATE INDEX ON "QRDinamico" ("activo");

CREATE INDEX ON "Pedido" ("id_local");

CREATE INDEX ON "Pedido" ("id_mesa");

CREATE INDEX ON "Pedido" ("id_usuario");

CREATE INDEX ON "Pedido" ("id_qr");

CREATE INDEX ON "Pedido" ("creado_por");

CREATE INDEX ON "Pedido" ("estado");

CREATE INDEX ON "Pedido" ("creado_el");

CREATE INDEX ON "Cuenta" ("id_pedido");

CREATE INDEX ON "Cuenta" ("id_producto");

CREATE INDEX ON "Cuenta" ("creado_por");

CREATE INDEX ON "EstadoPedido" ("id_pedido");

CREATE INDEX ON "EstadoPedido" ("creado_por");

CREATE INDEX ON "EstadoPedido" ("estado");

CREATE INDEX ON "EstadoPedido" ("creado_el");

CREATE INDEX ON "Encomienda" ("id_pedido");

CREATE INDEX ON "Encomienda" ("creado_el");

CREATE INDEX ON "EncomiendaCuenta" ("id_cuenta");

CREATE INDEX ON "EncomiendaCuenta" ("id_encomienda");

CREATE INDEX ON "Pago" ("id_pedido");

CREATE INDEX ON "Pago" ("creado_por");

CREATE INDEX ON "Pago" ("estado");

CREATE INDEX ON "Pago" ("creado_el");

ALTER TABLE "Direccion" ADD FOREIGN KEY ("id_comuna") REFERENCES "Comuna" ("id");

ALTER TABLE "Local" ADD FOREIGN KEY ("id_direccion") REFERENCES "Direccion" ("id");

ALTER TABLE "Local" ADD FOREIGN KEY ("id_tipo_local") REFERENCES "TipoLocal" ("id");

ALTER TABLE "Horario" ADD FOREIGN KEY ("id_local") REFERENCES "Local" ("id");

ALTER TABLE "Mesa" ADD FOREIGN KEY ("id_local") REFERENCES "Local" ("id");

ALTER TABLE "Usuario" ADD FOREIGN KEY ("id_rol") REFERENCES "Rol" ("id");

ALTER TABLE "Usuario" ADD FOREIGN KEY ("id_local") REFERENCES "Local" ("id");

ALTER TABLE "Foto" ADD FOREIGN KEY ("id_local") REFERENCES "Local" ("id");

ALTER TABLE "Foto" ADD FOREIGN KEY ("id_producto") REFERENCES "Producto" ("id");

ALTER TABLE "Foto" ADD FOREIGN KEY ("id_categoria") REFERENCES "Categoria" ("id");

ALTER TABLE "Foto" ADD FOREIGN KEY ("id_tipo_foto") REFERENCES "TipoFoto" ("id");

ALTER TABLE "Redes" ADD FOREIGN KEY ("id_local") REFERENCES "Local" ("id");

ALTER TABLE "Redes" ADD FOREIGN KEY ("id_tipo_red") REFERENCES "TipoRed" ("id");

ALTER TABLE "Redes" ADD FOREIGN KEY ("id_foto") REFERENCES "Foto" ("id");

ALTER TABLE "Producto" ADD FOREIGN KEY ("id_local") REFERENCES "Local" ("id");

ALTER TABLE "Producto" ADD FOREIGN KEY ("id_categoria") REFERENCES "Categoria" ("id");

ALTER TABLE "Opinion" ADD FOREIGN KEY ("id_usuario") REFERENCES "Usuario" ("id");

ALTER TABLE "Opinion" ADD FOREIGN KEY ("id_local") REFERENCES "Local" ("id");

ALTER TABLE "Favorito" ADD FOREIGN KEY ("id_usuario") REFERENCES "Usuario" ("id");

ALTER TABLE "Favorito" ADD FOREIGN KEY ("id_local") REFERENCES "Local" ("id");

ALTER TABLE "Reserva" ADD FOREIGN KEY ("id_local") REFERENCES "Local" ("id");

ALTER TABLE "Reserva" ADD FOREIGN KEY ("id_usuario") REFERENCES "Usuario" ("id");

ALTER TABLE "ReservaMesa" ADD FOREIGN KEY ("id_reserva") REFERENCES "Reserva" ("id");

ALTER TABLE "ReservaMesa" ADD FOREIGN KEY ("id_mesa") REFERENCES "Mesa" ("id");

ALTER TABLE "QRDinamico" ADD FOREIGN KEY ("id_mesa") REFERENCES "Mesa" ("id");

ALTER TABLE "QRDinamico" ADD FOREIGN KEY ("id_pedido") REFERENCES "Pedido" ("id");

ALTER TABLE "QRDinamico" ADD FOREIGN KEY ("id_reserva") REFERENCES "Reserva" ("id");

ALTER TABLE "QRDinamico" ADD FOREIGN KEY ("id_usuario") REFERENCES "Usuario" ("id");

ALTER TABLE "Pedido" ADD FOREIGN KEY ("id_local") REFERENCES "Local" ("id");

ALTER TABLE "Pedido" ADD FOREIGN KEY ("id_mesa") REFERENCES "Mesa" ("id");

ALTER TABLE "Pedido" ADD FOREIGN KEY ("id_usuario") REFERENCES "Usuario" ("id");

ALTER TABLE "Pedido" ADD FOREIGN KEY ("id_qr") REFERENCES "QRDinamico" ("id");

ALTER TABLE "Pedido" ADD FOREIGN KEY ("creado_por") REFERENCES "Usuario" ("id");

ALTER TABLE "Cuenta" ADD FOREIGN KEY ("id_pedido") REFERENCES "Pedido" ("id");

ALTER TABLE "Cuenta" ADD FOREIGN KEY ("id_producto") REFERENCES "Producto" ("id");

ALTER TABLE "Cuenta" ADD FOREIGN KEY ("creado_por") REFERENCES "Usuario" ("id");

ALTER TABLE "EstadoPedido" ADD FOREIGN KEY ("id_pedido") REFERENCES "Pedido" ("id");

ALTER TABLE "EstadoPedido" ADD FOREIGN KEY ("creado_por") REFERENCES "Usuario" ("id");

ALTER TABLE "Encomienda" ADD FOREIGN KEY ("id_pedido") REFERENCES "Pedido" ("id");

ALTER TABLE "EncomiendaCuenta" ADD FOREIGN KEY ("id_cuenta") REFERENCES "Cuenta" ("id");

ALTER TABLE "EncomiendaCuenta" ADD FOREIGN KEY ("id_encomienda") REFERENCES "Encomienda" ("id");

ALTER TABLE "Pago" ADD FOREIGN KEY ("id_pedido") REFERENCES "Pedido" ("id");

ALTER TABLE "Pago" ADD FOREIGN KEY ("creado_por") REFERENCES "Usuario" ("id");
