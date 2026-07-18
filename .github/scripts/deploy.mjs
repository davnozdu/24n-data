// Инкрементальная заливка 24n.cz через lftp (FTPS), Node.js.
//
// Почему lftp, а не basic-ftp: у этого хостинга basic-ftp падал на дата-канале
// с `ECONNRESET (data socket)` — он не переиспользует TLS-сессию контрольного
// канала на данных, и сервер сбрасывает пассивное соединение. lftp сессию
// переиспользует (set ftp:ssl-protect-data + ssl-force) и работает стабильно
// (та же схема, что уже проверена на appleplus.cz).
//
// mirror --reverse: заливает dist/ на сервер.
//  • обычный прогон — `--ignore-time`: сравнение по РАЗМЕРУ (регенерация dist не
//    плодит лишних аплоадов; уходят только реально изменившиеся файлы);
//  • DEPLOY_FORCE_FULL=true — без `--ignore-time`: сравнение по времени, а все
//    локальные файлы только что сгенерированы (mtime свежее) → переотправка всего.
// БЕЗ `--delete`: файлы, которых нет в локальном dist/ (старые статьи вне окна),
// на сервере СОХРАНЯЮТСЯ — постоянный архив; полноту карты даёт sitemap.php.

import { execFileSync } from "node:child_process";
import { join } from "node:path";

const {
  FTP_HOST,
  FTP_USER,
  FTP_PASSWORD,
  FTP_REMOTE_DIR = "/",
  FTP_PORT = "21",
  FTP_SECURE = "true",
  DIST_DIR = "dist",
  FORCE_FULL_DEPLOY = "false",
} = process.env;

if (!FTP_HOST || !FTP_USER || !FTP_PASSWORD) {
  console.error("Missing FTP_HOST / FTP_USER / FTP_PASSWORD");
  process.exit(1);
}

const secure = String(FTP_SECURE).toLowerCase() === "true";
const force = String(FORCE_FULL_DEPLOY).toLowerCase() === "true";
const port = Number(FTP_PORT) || 21;
const localDist = join(process.cwd(), DIST_DIR);
const remoteRoot = FTP_REMOTE_DIR.endsWith("/") ? FTP_REMOTE_DIR : FTP_REMOTE_DIR + "/";

// Настройки FTPS для lftp: принудительный TLS, защита данных (переиспользование
// сессии), без строгой проверки сертификата (у шаред-хостингов он часто общий).
const settings = [
  "set ssl:verify-certificate no",
  `set ftp:ssl-force ${secure ? "true" : "false"}`,
  "set ftp:ssl-protect-data true",
  "set net:max-retries 2",
  "set net:timeout 30",
  "set net:persist-retries 2",
  "set mirror:parallel-transfer-count 3",
  "set cmd:fail-exit yes",
];

const mirrorOpts = ["--reverse", "--no-perms", "--verbose"];
if (!force) mirrorOpts.push("--ignore-time"); // сравнение по размеру (минимум аплоадов)

// Все команды одной строкой через -e (host — последним аргументом: надёжный
// порядок, иначе lftp принимает host позиционно и ломается на -f). mirror сам
// создаёт недостающие каталоги на сервере — отдельный mkdir не нужен.
// lcd в dist + источник "." → на сервер уходит СОДЕРЖИМОЕ dist (в корень
// remoteRoot), а не папка dist. Заодно сносим возможную залежавшуюся подпапку
// dist на сервере и печатаем листинг корня для проверки.
const commands =
  [
    ...settings,
    `lcd "${localDist}"`,
    "set cmd:fail-exit no",
    `rm -rf "${remoteRoot}dist"`,
    // Дочистка СТАРОГО бренда 420N на сервере (деплой файлы не удаляет):
    // logo-crop*.png — прежний логотип, публично лежал в /assets/.
    `rm -f "${remoteRoot}assets/logo-crop.png"`,
    `rm -f "${remoteRoot}assets/logo-crop-white.png"`,
    "set cmd:fail-exit yes",
    `mirror ${mirrorOpts.join(" ")} . "${remoteRoot}"`,
    // Поисковый индекс Pagefind — ОТДЕЛЬНЫМ зеркалом БЕЗ --ignore-time и С
    // --delete: у служебных файлов (pagefind-entry.json с хэшем фиксированной
    // длины) размер часто не меняется, size-диф их пропускал — и поиск неделями
    // отдавал старый индекс. Каталог полностью наш (генерится каждый деплой),
    // поэтому старые чанки удаляем. Объём мал — переливка дешёвая.
    `mirror --reverse --delete --no-perms --verbose ./pagefind "${remoteRoot}pagefind"`,
    `echo === Содержимое корня ${remoteRoot} после заливки: ===`,
    `cls -1 "${remoteRoot}"`,
    "bye",
  ].join("; ");

console.log(
  `Deploying dist → ${FTP_HOST}:${port}${remoteRoot} via lftp ` +
    `(secure=${secure}${force ? ", FORCE FULL" : ", incremental by size"})…`
);

try {
  execFileSync(
    "lftp",
    ["-u", `${FTP_USER},${FTP_PASSWORD}`, "-p", String(port), "-e", commands, FTP_HOST],
    { stdio: "inherit" }
  );
  console.log("Done: dist залит (архив на сервере сохранён, ничего не удалено).");
} catch (err) {
  console.error("lftp deploy failed:", err?.message || err);
  process.exit(1);
}
