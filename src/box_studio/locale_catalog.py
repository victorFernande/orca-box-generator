"""Small offline language pack. Source phrases, units and placeholders stay explicit."""

from __future__ import annotations

SUPPORTED_LANGUAGES = ("pt", "en", "es", "it", "fr", "de", "ja")
LANGUAGE_NAMES = ("Português", "English", "Español", "Italiano", "Français", "Deutsch", "日本語")


def normalize_language(value: object, default: str = "pt") -> str:
    raw = str(value or "").strip().lower().replace("_", "-").split(".", 1)[0]
    if not raw:
        return default if default in SUPPORTED_LANGUAGES else "en"
    code = raw.split("-", 1)[0]
    return code if code in SUPPORTED_LANGUAGES else "en"


# English | Spanish | Italian | French | German | Japanese.
# Do not run this catalog over user names, printer names, paths or numeric inputs.
_ROWS = """
Enclosure|Caja|Scatola|Boîtier|Gehäuse|ケース
Features|Accesorios|Accessori|Accessoires|Zubehör|付属機能
Presets|Preajustes|Preimpostazioni|Préréglages|Vorlagen|プリセット
Construction|Construcción|Costruzione|Construction|Aufbau|構造
Enclosure style|Estilo de caja|Tipo di scatola|Style de boîtier|Gehäusetyp|ケースの種類
Open bin|Caja abierta|Contenitore aperto|Bac ouvert|Offene Box|オープンボックス
Latch lid|Tapa con cierres|Coperchio con chiusure|Couvercle à loquets|Deckel mit Verschlüssen|ラッチ付きのふた
Stackable bin|Caja apilable|Contenitore impilabile|Bac empilable|Stapelbox|積み重ねボックス
PIP clamshell|Estuche articulado PIP|Custodia incernierata PIP|Étui articulé PIP|PIP-Klappbox|一体造形の開閉ケース
Hinged assembly|Conjunto articulado|Assieme incernierato|Ensemble articulé|Scharnierbaugruppe|ヒンジ付きアセンブリ
Equal halves · closed height: {height} mm. The assembly prints open at 180°.|Mitades iguales · altura cerrada: {height} mm. Se imprime abierto a 180°.|Metà uguali · altezza chiusa: {height} mm. Si stampa aperto a 180°.|Moitiés égales · hauteur fermée : {height} mm. Impression ouverte à 180°.|Gleiche Hälften · geschlossene Höhe: {height} mm. Druck um 180° geöffnet.|上下同じ深さ・閉じた高さ: {height} mm。180°開いた状態で印刷します。
Open footprint on the bed: {size} mm.|Huella abierta en la cama: {size} mm.|Ingombro aperto sul piatto: {size} mm.|Encombrement ouvert sur le plateau : {size} mm.|Offene Stellfläche auf dem Druckbett: {size} mm.|開いた状態の設置寸法: {size} mm。
Remove existing standoffs, cutouts, dividers and TPU features to use this style.|Elimina los soportes, recortes, divisores y elementos TPU para usar este estilo.|Rimuovi supporti, aperture, divisori e parti TPU per usare questo tipo.|Retirez les entretoises, découpes, cloisons et éléments TPU pour utiliser ce style.|Für diesen Typ vorhandene Abstandshalter, Ausschnitte, Trennwände und TPU-Elemente entfernen.|この種類では、支柱、開口部、仕切り、TPU部品を削除してください。
Total height includes the foot. To stack different heights, keep X/Y dimensions, corners, walls and mating features identical.|La altura total incluye el pie. Para apilar alturas distintas, mantén iguales X/Y, esquinas, paredes y encajes.|L'altezza totale include il piede. Per impilare altezze diverse, mantieni uguali X/Y, angoli, pareti e incastri.|La hauteur totale inclut le pied. Pour empiler différentes hauteurs, gardez les mêmes dimensions X/Y, angles, parois et emboîtements.|Die Gesamthöhe umfasst den Fuß. Für unterschiedliche Stapelhöhen X/Y, Ecken, Wände und Passungen gleich halten.|全高には脚を含みます。高さの異なる箱を積む場合、X/Y寸法、角、壁、はめ合い部を同じにしてください。
Connections & grips|Encajes y asas|Incastri e maniglie|Assemblages et poignées|Verbindungen und Griffe|はめ合いと持ち手
Hand grips|Asas de mano|Maniglie|Poignées|Handgriffe|持ち手
Pair of faces|Par de caras|Coppia di facce|Paire de faces|Flächenpaar|取り付け面の組
Left / right|Izquierda / derecha|Sinistra / destra|Gauche / droite|Links / rechts|左 / 右
Front / back|Frente / atrás|Fronte / retro|Avant / arrière|Vorne / hinten|前 / 後
Two latches pivot on the base, each with a grip and hook. Release them before lifting off the lid.|Dos cierres giran sobre la base, cada uno con asa y gancho. Libéralos antes de levantar la tapa.|Due chiusure ruotano sulla base, ciascuna con presa e gancio. Sganciale prima di sollevare il coperchio.|Deux loquets pivotent sur la base, chacun avec une prise et un crochet. Libérez-les avant de soulever le couvercle.|Zwei Verschlüsse mit Griff und Haken schwenken an der Basis. Vor dem Abheben des Deckels lösen.|持ち手とフック付きの2つのラッチが底部で回転します。ふたを持ち上げる前に解除してください。
Release latches & open|Soltar cierres y abrir|Sgancia e apri|Libérer les loquets et ouvrir|Verschlüsse lösen und öffnen|ラッチを解除して開く
Rotate latches & open|Girar cierres y abrir|Ruota le chiusure e apri|Tourner les loquets et ouvrir|Verschlüsse drehen und öffnen|ラッチを回して開く
Latches engaged · lid closed|Cierres enganchados · tapa cerrada|Chiusure agganciate · coperchio chiuso|Loquets engagés · couvercle fermé|Verschlüsse eingerastet · Deckel geschlossen|ラッチ固定・ふたは閉じています
Rotating latches · lid stationary|Girando cierres · tapa inmóvil|Rotazione chiusure · coperchio fermo|Rotation des loquets · couvercle immobile|Verschlüsse drehen · Deckel steht|ラッチ回転中・ふたは固定
Latches open · opening the lid|Cierres abiertos · abriendo tapa|Chiusure aperte · apertura coperchio|Loquets ouverts · ouverture du couvercle|Verschlüsse offen · Deckel öffnet|ラッチ解除・ふたを開いています
Latches open · lid open|Cierres abiertos · tapa abierta|Chiusure aperte · coperchio aperto|Loquets ouverts · couvercle ouvert|Verschlüsse offen · Deckel offen|ラッチ解除・ふたは開いています
Releasing latches · lid stationary|Soltando cierres · tapa inmóvil|Sgancio chiusure · coperchio fermo|Libération des loquets · couvercle immobile|Verschlüsse lösen · Deckel steht|ラッチ解除中・ふたは固定
Latches open · lifting the lid|Cierres abiertos · levantando tapa|Chiusure aperte · sollevamento coperchio|Loquets ouverts · levée du couvercle|Verschlüsse offen · Deckel wird angehoben|ラッチ解除・ふたを持ち上げています
Latches open · lid removed|Cierres abiertos · tapa retirada|Chiusure aperte · coperchio rimosso|Loquets ouverts · couvercle retiré|Verschlüsse offen · Deckel abgenommen|ラッチ解除・ふたを外しました
Latch motion unavailable. Regenerate the preview.|Movimiento de cierres no disponible. Regenera la vista previa.|Movimento delle chiusure non disponibile. Rigenera l'anteprima.|Mouvement des loquets indisponible. Régénérez l'aperçu.|Verschlussbewegung nicht verfügbar. Vorschau neu erzeugen.|ラッチの動作を表示できません。プレビューを再生成してください。
Width X|Ancho X|Larghezza X|Largeur X|Breite X|幅 X
Depth Y|Profundidad Y|Profondità Y|Profondeur Y|Tiefe Y|奥行き Y
Base height Z|Altura de base Z|Altezza base Z|Hauteur de base Z|Basishöhe Z|底部の高さ Z
Height Z|Altura Z|Altezza Z|Hauteur Z|Höhe Z|高さ Z
Height of each half Z|Altura de cada mitad Z|Altezza di ogni metà Z|Hauteur de chaque moitié Z|Höhe jeder Hälfte Z|各半分の高さ Z
Total height Z|Altura total Z|Altezza totale Z|Hauteur totale Z|Gesamthöhe Z|全高 Z
Corner radius|Radio de esquina|Raggio degli angoli|Rayon des angles|Eckenradius|角の半径
Wall|Pared|Parete|Paroi|Wand|壁
Floor|Fondo|Fondo|Fond|Boden|底
Lid thickness|Espesor de tapa|Spessore coperchio|Épaisseur du couvercle|Deckelstärke|ふたの厚さ
Lid height|Altura de tapa|Altezza coperchio|Hauteur du couvercle|Deckelhöhe|ふたの高さ
Clearance per side|Holgura por lado|Gioco per lato|Jeu par côté|Spiel je Seite|片側のクリアランス
Gap between halves Z|Holgura entre mitades Z|Gioco tra le metà Z|Jeu entre les moitiés Z|Spalt zwischen Hälften Z|上下間の隙間 Z
Joint clearance|Holgura de encaje|Gioco degli incastri|Jeu des assemblages|Passungsspiel|接合部のクリアランス
Hinge clearance|Holgura de bisagra|Gioco cerniera|Jeu de charnière|Scharnierspiel|ヒンジのクリアランス
Pivot clearance|Holgura de pivotes|Gioco dei perni|Jeu des pivots|Drehzapfenspiel|軸のクリアランス
Locating skirt depth|Profundidad del faldón guía|Profondità del bordo guida|Profondeur de la jupe de centrage|Tiefe des Führungsrandes|位置決めスカートの深さ
Hinge|Bisagra|Cerniera|Charnière|Scharnier|ヒンジ
Pin diameter|Diámetro de pasador|Diametro del perno|Diamètre de l'axe|Stiftdurchmesser|ピンの直径
Integral axle diameter|Diámetro de eje integrado|Diametro dell'asse integrato|Diamètre de l'axe intégré|Durchmesser der integrierten Achse|一体軸の直径
Corner screw|Tornillo de esquina|Vite d'angolo|Vis d'angle|Eckschraube|角のねじ
Surface resolution|Resolución de superficie|Risoluzione superficie|Résolution de surface|Oberflächenauflösung|表面の解像度
Standard|Estándar|Standard|Standard|Standard|標準
Fine|Fina|Fine|Fine|Fein|高精細
TPU gasket|Junta TPU|Guarnizione TPU|Joint TPU|TPU-Dichtung|TPUガスケット
Perimeter channel and gasket|Canal perimetral y junta|Canale perimetrale e guarnizione|Rainure périphérique et joint|Umlaufende Nut und Dichtung|外周溝とガスケット
Channel width|Ancho del canal|Larghezza canale|Largeur de rainure|Nutbreite|溝の幅
Channel depth|Profundidad del canal|Profondità canale|Profondeur de rainure|Nuttiefe|溝の深さ
Export the gasket separately and select TPU in the slicer. Physical sealing requires testing.|Exporta la junta por separado y selecciona TPU en el laminador. La estanqueidad requiere pruebas.|Esporta la guarnizione separatamente e seleziona TPU nello slicer. La tenuta richiede prove fisiche.|Exportez le joint séparément et choisissez le TPU dans le trancheur. L'étanchéité doit être testée.|Dichtung separat exportieren und TPU im Slicer wählen. Dichtheit muss praktisch geprüft werden.|ガスケットを別に書き出し、スライサーでTPUを選択してください。密閉性は実物での試験が必要です。
PCB & placement|PCB y posición|PCB e posizionamento|PCB et placement|PCB und Platzierung|基板と配置
Drag standoffs. Centered origin; X right, Y back. Exact coordinates remain editable below.|Arrastra los soportes. Origen centrado; X a la derecha, Y hacia atrás. Las coordenadas exactas se editan abajo.|Trascina i supporti. Origine centrata; X a destra, Y verso il retro. Le coordinate esatte sono modificabili sotto.|Déplacez les entretoises. Origine centrée ; X à droite, Y vers l'arrière. Les coordonnées exactes restent modifiables ci-dessous.|Abstandshalter ziehen. Ursprung mittig; X nach rechts, Y nach hinten. Genaue Koordinaten sind unten editierbar.|支柱をドラッグします。原点は中央、Xは右、Yは後方です。正確な座標は下で編集できます。
Panel cutouts|Recortes del panel|Aperture pannello|Découpes du panneau|Plattenausschnitte|パネルの開口部
Real through-openings. Preserve corners, floor and lid interface. Connector dimensions are editable starting points.|Aberturas pasantes reales. Conserva esquinas, fondo y encaje de tapa. Las medidas de conectores son valores iniciales editables.|Aperture passanti reali. Preserva angoli, fondo e giunzione del coperchio. Le misure dei connettori sono valori iniziali modificabili.|Ouvertures traversantes réelles. Préservez angles, fond et assemblage du couvercle. Les dimensions des connecteurs sont des valeurs initiales modifiables.|Echte Durchbrüche. Ecken, Boden und Deckelpassung erhalten. Anschlussmaße sind editierbare Ausgangswerte.|実際に貫通する開口部です。角、底、ふたの接合部を確保してください。コネクター寸法は編集可能な初期値です。
Dividers|Divisores|Divisori|Cloisons|Trennwände|仕切り
X positions, comma separated|Posiciones X, separadas por comas|Posizioni X, separate da virgole|Positions X, séparées par des virgules|X-Positionen, durch Kommas getrennt|X位置、カンマ区切り
Y positions, comma separated|Posiciones Y, separadas por comas|Posizioni Y, separate da virgole|Positions Y, séparées par des virgules|Y-Positionen, durch Kommas getrennt|Y位置、カンマ区切り
Design library|Biblioteca de diseños|Libreria progetti|Bibliothèque de modèles|Entwurfsbibliothek|デザインライブラリ
My presets|Mis preajustes|Le mie preimpostazioni|Mes préréglages|Meine Vorlagen|自分のプリセット
Save|Guardar|Salva|Enregistrer|Speichern|保存
PCB envelopes are references. Check your actual board model and revision.|Los contornos de PCB son referencias. Comprueba el modelo y revisión de tu placa.|Gli ingombri PCB sono indicativi. Verifica modello e revisione della tua scheda.|Les contours PCB sont indicatifs. Vérifiez le modèle et la révision de votre carte.|PCB-Umrisse dienen als Referenz. Tatsächliches Modell und Revision prüfen.|基板外形は参考です。実際の基板のモデルとリビジョンを確認してください。
Open|Abrir|Apri|Ouvrir|Öffnen|開く
Inspection|Inspección|Ispezione|Inspection|Prüfung|検査
Volume · cm³|Volumen · cm³|Volume · cm³|Volume · cm³|Volumen · cm³|体積 · cm³
Triangles|Triángulos|Triangoli|Triangles|Dreiecke|三角形
X-ray · internal components|Rayos X · componentes internos|Raggi X · componenti interni|Rayons X · composants internes|Röntgen · innere Bauteile|X線・内部部品
Axial inspection cut|Corte axial de inspección|Sezione assiale di ispezione|Coupe axiale d'inspection|Axialer Prüfschnitt|軸方向の断面検査
Preview and export share the Python geometry. Curves are tessellated; model updates run in the background.|La vista previa y la exportación comparten la geometría Python. Las curvas se triangulan y los cambios se calculan en segundo plano.|Anteprima ed esportazione condividono la geometria Python. Le curve sono tessellate e gli aggiornamenti avvengono in background.|Aperçu et export partagent la géométrie Python. Les courbes sont tessellées ; les mises à jour s'exécutent en arrière-plan.|Vorschau und Export nutzen dieselbe Python-Geometrie. Kurven werden tesselliert; Aktualisierungen laufen im Hintergrund.|プレビューと書き出しは同じPython形状を使用します。曲線は分割され、モデルの更新はバックグラウンドで実行されます。
Manufacture|Fabricación|Produzione|Fabrication|Fertigung|製造
Base + lid|Base + tapa|Base + coperchio|Base + couvercle|Basis + Deckel|底部 + ふた
Base only|Solo base|Solo base|Base seule|Nur Basis|底部のみ
Lid only|Solo tapa|Solo coperchio|Couvercle seul|Nur Deckel|ふたのみ
Fit calibration kit|Kit de calibración de encaje|Kit di calibrazione incastri|Kit de calibrage des ajustements|Passungs-Kalibriersatz|はめ合い調整キット
Complete set|Conjunto completo|Set completo|Ensemble complet|Komplettsatz|全パーツ
Send to Plater|Enviar a la mesa|Invia al piatto|Envoyer au plateau|An Druckbett senden|プレートに送る
Apply mechanical slicing|Aplicar ajustes mecánicos|Applica impostazioni meccaniche|Appliquer les réglages mécaniques|Mechanische Druckeinstellungen anwenden|機械部品用の印刷設定を適用
Open export folder|Abrir carpeta de exportación|Apri cartella esportazioni|Ouvrir le dossier d'export|Exportordner öffnen|書き出しフォルダーを開く
Base on its floor; preserve the exported orientation of each part. Print the fit kit first. Print time depends on printer and profile.|Base sobre el fondo; conserva la orientación exportada de cada pieza. Imprime primero el kit de encaje. El tiempo depende de la impresora y del perfil.|Base sul fondo; conserva l'orientamento esportato di ogni parte. Stampa prima il kit di incastro. Il tempo dipende da stampante e profilo.|Base sur son fond ; conservez l'orientation exportée de chaque pièce. Imprimez d'abord le kit d'ajustement. Le temps dépend de l'imprimante et du profil.|Basis auf den Boden stellen; exportierte Ausrichtung jeder Komponente beibehalten. Zuerst Passungssatz drucken. Druckzeit hängt von Drucker und Profil ab.|底部を下にし、各部品の書き出し時の向きを維持してください。最初にはめ合いキットを印刷してください。印刷時間はプリンターと設定によります。
Base and lid have independent heights. Export all four parts: shells with their outer faces on the bed, latches flat. Snap the spherical joints together after printing; check your filament's flexibility.|Base y tapa tienen alturas independientes. Exporta las cuatro piezas: caras externas de las carcasas sobre la cama y cierres planos. Encaja las uniones esféricas tras imprimir; comprueba la flexibilidad del filamento.|Base e coperchio hanno altezze indipendenti. Esporta le quattro parti: gusci con facce esterne sul piatto, chiusure distese. Assembla gli snodi sferici dopo la stampa e verifica la flessibilità del filamento.|Base et couvercle ont des hauteurs indépendantes. Exportez les quatre pièces : faces extérieures des coques sur le plateau, loquets à plat. Emboîtez les rotules après impression ; vérifiez la souplesse du filament.|Basis und Deckel haben unabhängige Höhen. Alle vier Teile exportieren: Schalen außen auf dem Druckbett, Verschlüsse flach. Kugelgelenke nach dem Druck einrasten; Filamentflexibilität prüfen.|底部とふたの高さは個別に設定できます。4部品すべてを書き出し、外面を下にしてラッチは平置きします。印刷後に球状接合部をはめ込み、フィラメントの柔軟性を確認してください。
Base and lid have equal height. Export the hinged assembly open at 180°, both outer faces on the bed. Keep that pose in the slicer and check the printed hinge.|Base y tapa tienen igual altura. Exporta el conjunto abierto a 180°, con ambas caras externas sobre la cama. Mantén esa posición y comprueba la bisagra impresa.|Base e coperchio hanno uguale altezza. Esporta l'assieme aperto a 180°, con entrambe le facce esterne sul piatto. Mantieni la posa nello slicer e verifica la cerniera stampata.|Base et couvercle ont la même hauteur. Exportez l'ensemble ouvert à 180°, les deux faces extérieures sur le plateau. Conservez cette position et vérifiez la charnière imprimée.|Basis und Deckel sind gleich hoch. Baugruppe um 180° geöffnet mit beiden Außenseiten auf dem Druckbett exportieren. Position im Slicer beibehalten und gedrucktes Scharnier prüfen.|底部とふたは同じ高さです。180°開いて両方の外面を下にした状態で書き出します。スライサーで向きを維持し、印刷したヒンジを確認してください。
Base floor down, opening upwards. Check the walls and the bridges above hand grips, when enabled, in the slicer preview.|Fondo abajo y abertura arriba. Comprueba paredes y puentes sobre las asas, si están activadas, en la vista del laminador.|Fondo in basso, apertura in alto. Verifica pareti e ponti sopra le maniglie, se attive, nell'anteprima dello slicer.|Fond vers le bas, ouverture vers le haut. Vérifiez les parois et les ponts au-dessus des poignées, si activées, dans l'aperçu du trancheur.|Boden nach unten, Öffnung nach oben. Wände und gegebenenfalls Brücken über den Handgriffen in der Slicer-Vorschau prüfen.|底を下、開口部を上にします。壁と、有効にした持ち手の上のブリッジをスライサーで確認してください。
Print with the foot on the bed and the front open. Total height includes the foot. Test the fit between bins of the same family before stacking.|Imprime con el pie en la cama y el frente abierto. La altura incluye el pie. Prueba el encaje entre cajas de la misma familia antes de apilarlas.|Stampa con il piede sul piatto e il fronte aperto. L'altezza include il piede. Prova l'incastro tra contenitori della stessa famiglia prima di impilarli.|Imprimez le pied sur le plateau et l'avant ouvert. La hauteur inclut le pied. Testez l'emboîtement des bacs de même famille avant de les empiler.|Mit Fuß auf dem Druckbett und offener Front drucken. Gesamthöhe umfasst den Fuß. Vor dem Stapeln die Passung derselben Boxfamilie prüfen.|脚をプレートに付け、前を開けて印刷します。全高には脚を含みます。積み重ねる前に同じ系列の箱同士のはめ合いを確認してください。
Set: base, lid and two latches. Print the shells on their outer faces and the latches upright. Fit the latches onto the base pivots; release the hooks before lifting the lid. Check the fit of the printed parts.|Conjunto: base, tapa y dos cierres. Imprime las carcasas sobre sus caras externas y los cierres de pie. Encaja los cierres en los pivotes de la base; libera los ganchos antes de levantar la tapa. Comprueba el encaje impreso.|Set: base, coperchio e due chiusure. Stampa i gusci sulle facce esterne e le chiusure in verticale. Monta le chiusure sui perni della base; sgancia i ganci prima di sollevare il coperchio. Verifica gli incastri stampati.|Ensemble : base, couvercle et deux loquets. Imprimez les coques sur leurs faces extérieures et les loquets debout. Montez les loquets sur les pivots de la base ; libérez les crochets avant de soulever le couvercle. Vérifiez l'ajustement imprimé.|Satz: Basis, Deckel und zwei Verschlüsse. Schalen auf den Außenseiten und Verschlüsse aufrecht drucken. Verschlüsse auf Basiszapfen setzen; Haken vor dem Abheben lösen. Gedruckte Passungen prüfen.|底部、ふた、2つのラッチのセットです。外殻は外面を下に、ラッチは立てて印刷します。ラッチを底部の軸に取り付け、ふたを上げる前にフックを外してください。印刷後のはめ合いを確認してください。
Drag to orbit · wheel to zoom|Arrastra para girar · rueda para zoom|Trascina per ruotare · rotella per zoom|Glisser pour tourner · molette pour zoomer|Ziehen zum Drehen · Mausrad zum Zoomen|ドラッグで回転・ホイールでズーム
Generating mesh… you can keep editing.|Generando malla… puedes seguir editando.|Generazione mesh… puoi continuare a modificare.|Génération du maillage… vous pouvez continuer à modifier.|Netz wird erzeugt… Bearbeitung bleibt möglich.|メッシュ生成中…編集を続けられます。
Mesh updated · ready to inspect.|Malla actualizada · lista para inspección.|Mesh aggiornata · pronta per l'ispezione.|Maillage actualisé · prêt à inspecter.|Netz aktualisiert · bereit zur Prüfung.|メッシュを更新しました・検査できます。
Interface preview. Open this plugin in OrcaSlicer to generate meshes.|Vista de la interfaz. Abre este plugin en OrcaSlicer para generar mallas.|Anteprima interfaccia. Apri il plugin in OrcaSlicer per generare le mesh.|Aperçu de l'interface. Ouvrez ce plugin dans OrcaSlicer pour générer des maillages.|Oberflächenvorschau. Zum Erzeugen von Netzen dieses Plugin in OrcaSlicer öffnen.|インターフェースのプレビューです。メッシュ生成にはOrcaSlicerでプラグインを開いてください。
Print-in-place: assembled set. Assess bridging/removable support below the lid without filling hinge gaps. Remove clips before opening.|Print-in-place: conjunto montado. Evalúa puentes o soportes extraíbles bajo la tapa sin llenar las holguras. Retira los clips antes de abrir.|Print-in-place: assieme montato. Valuta ponti o supporti rimovibili sotto il coperchio senza riempire i giochi delle cerniere. Rimuovi le clip prima di aprire.|Impression en place : ensemble assemblé. Évaluez les ponts ou supports amovibles sous le couvercle sans remplir les jeux des charnières. Retirez les clips avant d'ouvrir.|Print-in-place: montierte Baugruppe. Brücken oder entfernbare Stützen unter dem Deckel prüfen, ohne Scharnierspalte zu füllen. Clips vor dem Öffnen entfernen.|一体造形の組立済みセットです。ヒンジの隙間を埋めないよう、ふたの下のブリッジや除去可能なサポートを確認してください。開く前にクリップを外してください。
Remove|Eliminar|Rimuovi|Retirer|Entfernen|削除
Post height|Altura del soporte|Altezza supporto|Hauteur d'entretoise|Abstandshalterhöhe|支柱の高さ
Outer Ø|Ø exterior|Ø esterno|Ø extérieur|Außen-Ø|外径
Hole Ø|Ø del agujero|Ø foro|Ø du trou|Bohrungs-Ø|穴径
Hole depth|Profundidad del agujero|Profondità foro|Profondeur du trou|Bohrungstiefe|穴の深さ
Insert|Inserto|Inserto|Insert|Gewindeeinsatz|インサート
Pilot|Agujero piloto|Foro pilota|Avant-trou|Kernloch|下穴
Face|Cara|Faccia|Face|Seite|面
Type|Tipo|Tipo|Type|Typ|種類
Front|Frente|Fronte|Avant|Vorne|前
Back|Atrás|Retro|Arrière|Hinten|後
Left|Izquierda|Sinistra|Gauche|Links|左
Right|Derecha|Destra|Droite|Rechts|右
SnapLock: snap-assembled rear hinge and two latches pivoting on the lid. No loose pins.|SnapLock: bisagra trasera de encaje y dos cierres giratorios en la tapa. Sin pasadores sueltos.|SnapLock: cerniera posteriore a scatto e due chiusure sul coperchio. Nessun perno separato.|SnapLock : charnière arrière emboîtable et deux loquets pivotant sur le couvercle. Aucun axe libre.|SnapLock: hinteres Schnappscharnier und zwei am Deckel schwenkende Verschlüsse. Keine losen Stifte.|SnapLock: はめ込み式の後部ヒンジと、ふた上で回転する2つのラッチです。別のピンは不要です。
Clearance enlarges the ear recesses while retaining the backing wall. The V rim keeps nominal contact.|La holgura amplía los huecos de las orejetas sin eliminar la pared posterior. El borde en V mantiene el contacto nominal.|Il gioco amplia le sedi delle alette mantenendo la parete posteriore. Il bordo a V mantiene il contatto nominale.|Le jeu agrandit les logements des oreilles en conservant la paroi arrière. Le bord en V garde le contact nominal.|Das Spiel vergrößert die Laschenaussparungen bei erhaltener Rückwand. Der V-Rand behält den Nennkontakt.|クリアランスは裏壁を残しながら耳部のくぼみを広げます。V字の縁は公称接触を維持します。
Grip clear width|Ancho libre del asa|Larghezza utile maniglia|Largeur libre de poignée|Freie Griffbreite|持ち手の開口幅
Grip clear height|Altura libre del asa|Altezza utile maniglia|Hauteur libre de poignée|Freie Griffhöhe|持ち手の開口高さ
Distance from top|Distancia desde arriba|Distanza dal bordo superiore|Distance depuis le haut|Abstand von oben|上端からの距離
Lid skirt depth|Profundidad del faldón|Profondità bordo coperchio|Profondeur de jupe du couvercle|Tiefe des Deckelrandes|ふたのスカートの深さ
Latch width|Ancho del cierre|Larghezza chiusura|Largeur du loquet|Verschlussbreite|ラッチの幅
Latch body thickness|Espesor del cierre|Spessore chiusura|Épaisseur du loquet|Verschlussstärke|ラッチ本体の厚さ
Hook engagement|Enganche del gancho|Presa del gancio|Engagement du crochet|Hakeneingriff|フックのかかり
Latch pivot diameter|Diámetro del pivote|Diametro perno chiusura|Diamètre du pivot de loquet|Verschluss-Zapfendurchmesser|ラッチ軸の直径
Snap interference|Interferencia del encaje|Interferenza dello scatto|Interférence du clipsage|Schnappübermaß|スナップの干渉量
Front access width|Ancho del acceso frontal|Larghezza accesso frontale|Largeur d'accès frontal|Breite der Frontöffnung|前部開口の幅
Front opening drop from top|Rebaje frontal desde arriba|Ribassamento frontale dall'alto|Abaissement frontal depuis le haut|Absenkung der Frontöffnung|上端からの前部開口の深さ
Stacking foot height|Altura del pie de apilado|Altezza piede di impilamento|Hauteur du pied d'empilage|Höhe des Stapelfußes|積み重ね用脚の高さ
Stacking clearance per side|Holgura de apilado por lado|Gioco di impilamento per lato|Jeu d'empilage par côté|Stapelspiel je Seite|積み重ね部の片側クリアランス
PIP hinge clearance|Holgura de bisagra PIP|Gioco cerniera PIP|Jeu de charnière PIP|PIP-Scharnierspiel|一体造形ヒンジのクリアランス
Hinge separation|Separación de bisagra|Distanza cerniera|Écartement de charnière|Scharnierabstand|ヒンジの間隔
TPU channel width|Ancho del canal TPU|Larghezza canale TPU|Largeur de rainure TPU|TPU-Nutbreite|TPU溝の幅
Parameters|Parámetros|Parametri|Paramètres|Parameter|パラメーター
Export|Exportar|Esporta|Exporter|Exportieren|書き出し
Model Gallery|Galería de modelos|Galleria modelli|Galerie de modèles|Modellgalerie|モデルギャラリー
+ Save|+ Guardar|+ Salva|+ Enregistrer|+ Speichern|+ 保存
All|Todos|Tutti|Tous|Alle|すべて
Mine|Míos|Miei|Les miens|Eigene|自分のもの
Shape|Forma|Forma|Forme|Form|形状
Print|Imprimir|Stampa|Imprimer|Drucken|印刷
Mesh inspection|Inspección de malla|Ispezione mesh|Inspection du maillage|Netzprüfung|メッシュ検査
Wall / Floor|Pared / Fondo|Parete / Fondo|Paroi / Fond|Wand / Boden|壁 / 底
Current scene (mm)|Escena actual (mm)|Scena attuale (mm)|Scène actuelle (mm)|Aktuelle Szene (mm)|現在のシーン (mm)
Mesh overhang|Voladizo de malla|Sbalzo mesh|Surplomb du maillage|Netzüberhang|メッシュのオーバーハング
Solid volume (cm³)|Volumen sólido (cm³)|Volume solido (cm³)|Volume solide (cm³)|Festkörpervolumen (cm³)|ソリッド体積 (cm³)
Orca Emerald Silk|Seda esmeralda Orca|Seta smeraldo Orca|Soie émeraude Orca|Orca-Smaragdseide|Orcaエメラルドシルク
Terracotta Ceramic|Cerámica terracota|Ceramica terracotta|Céramique terre cuite|Terrakotta-Keramik|テラコッタセラミック
Matte White Porcelain|Porcelana blanca mate|Porcellana bianca opaca|Porcelaine blanche mate|Mattweißes Porzellan|マットな白磁
Brushed Copper Bronze|Bronce cobrizo cepillado|Bronzo ramato spazzolato|Bronze cuivré brossé|Gebürstete Kupferbronze|ヘアライン銅青銅
🔬 X-Ray / Wall (Translucent)|🔬 Rayos X / pared (translúcida)|🔬 Raggi X / parete (traslucida)|🔬 Rayons X / paroi (translucide)|🔬 Röntgen / Wand (durchscheinend)|🔬 X線 / 壁（半透明）
Overhang Map (°)|Mapa de voladizos (°)|Mappa sbalzi (°)|Carte des surplombs (°)|Überhangkarte (°)|オーバーハングマップ (°)
🔬 X-Ray / Wall|🔬 Rayos X / pared|🔬 Raggi X / parete|🔬 Rayons X / paroi|🔬 Röntgen / Wand|🔬 X線 / 壁
📏 Calipers mm|📏 Calibre mm|📏 Calibro mm|📏 Pied à coulisse mm|📏 Messschieber mm|📏 ノギス mm
🔥 Overhang|🔥 Voladizo|🔥 Sbalzo|🔥 Surplomb|🔥 Überhang|🔥 オーバーハング
⌗ Mesh|⌗ Malla|⌗ Mesh|⌗ Maillage|⌗ Netz|⌗ メッシュ
Top|Arriba|Alto|Dessus|Oben|上
Bottom|Abajo|Basso|Dessous|Unten|下
Fit|Encuadrar|Inquadra|Cadrer|Einpassen|全体表示
✂ Vertical Cut Y|✂ Corte vertical Y|✂ Sezione verticale Y|✂ Coupe verticale Y|✂ Vertikalschnitt Y|✂ 垂直断面 Y
💿 Horizontal Slice Z|💿 Corte horizontal Z|💿 Sezione orizzontale Z|💿 Coupe horizontale Z|💿 Horizontalschnitt Z|💿 水平断面 Z
Outer|Exterior|Esterno|Extérieur|Außen|外側
Cavity & Floor|Cavidad y fondo|Cavità e fondo|Cavité et fond|Hohlraum und Boden|空洞と底
Send to OrcaSlicer Plater|Enviar a la mesa de OrcaSlicer|Invia al piatto di OrcaSlicer|Envoyer au plateau OrcaSlicer|An OrcaSlicer-Druckbett senden|OrcaSlicerのプレートに送る
Export .3MF|Exportar .3MF|Esporta .3MF|Exporter .3MF|.3MF exportieren|.3MFを書き出す
Export .STL|Exportar .STL|Esporta .STL|Exporter .STL|.STL exportieren|.STLを書き出す
Surprise me|Sorpréndeme|Sorprendimi|Surprenez-moi|Überrasche mich|ランダム生成
Snap-fit lid box|Caja con tapa de encaje|Scatola con coperchio a scatto|Boîte à couvercle clipsé|Box mit Schnappdeckel|スナップ式ふた付きボックス
Screw-lid box|Caja con tapa atornillada|Scatola con coperchio avvitato|Boîte à couvercle vissé|Box mit Schraubdeckel|ねじ止め式ふた付きボックス
Rugged box · SnapLock|Caja reforzada · SnapLock|Scatola rinforzata · SnapLock|Boîte renforcée · SnapLock|Robuste Box · SnapLock|頑丈なボックス · SnapLock
Sliding-lid box|Caja con tapa deslizante|Scatola con coperchio scorrevole|Boîte à couvercle coulissant|Box mit Schiebedeckel|スライド式ふた付きボックス
Open bin with hand grips|Caja abierta con asas|Contenitore aperto con maniglie|Bac ouvert à poignées|Offene Box mit Griffen|持ち手付きオープンボックス
Removable lid · pivoting latches|Tapa extraíble · cierres giratorios|Coperchio rimovibile · chiusure girevoli|Couvercle amovible · loquets pivotants|Abnehmbarer Deckel · Schwenkverschlüsse|取り外し式ふた · 回転ラッチ
Stackable organizer · front access|Organizador apilable · acceso frontal|Contenitore impilabile · accesso frontale|Organiseur empilable · accès frontal|Stapelbarer Organizer · Frontöffnung|積み重ね収納 · 前部開口
Print-in-place clamshell|Estuche articulado print-in-place|Custodia incernierata print-in-place|Étui articulé imprimé en place|Print-in-place-Klappbox|一体造形の開閉ケース
Curved interface chord-error target ≤ {error} mm|Error objetivo de interfaces curvas ≤ {error} mm|Errore obiettivo delle interfacce curve ≤ {error} mm|Erreur cible des interfaces courbes ≤ {error} mm|Ziel-Sehnenfehler gekrümmter Passungen ≤ {error} mm|曲面接合部の弦誤差目標 ≤ {error} mm
Closed: {height} mm · base {base} + lid {lid} mm|Cerrada: {height} mm · base {base} + tapa {lid} mm|Chiusa: {height} mm · base {base} + coperchio {lid} mm|Fermée : {height} mm · base {base} + couvercle {lid} mm|Geschlossen: {height} mm · Basis {base} + Deckel {lid} mm|閉じた高さ: {height} mm · 底部 {base} + ふた {lid} mm
walls of|perímetros de|perimetri da|périmètres de|Wände mit|周の外周線・線幅
Mode|Modo|Modalità|Mode|Modus|モード
Reset|Restablecer|Ripristina|Réinitialiser|Zurücksetzen|リセット
Undo|Deshacer|Annulla|Annuler|Rückgängig|元に戻す
Redo|Rehacer|Ripeti|Rétablir|Wiederholen|やり直す
Language|Idioma|Lingua|Langue|Sprache|言語
Theme|Tema|Tema|Thème|Design|テーマ
Name|Nombre|Nome|Nom|Name|名前
Preset name|Nombre del preajuste|Nome preimpostazione|Nom du préréglage|Vorlagenname|プリセット名
Base|Base|Base|Base|Basis|底部
Lid|Tapa|Coperchio|Couvercle|Deckel|ふた
Left latch|Cierre izquierdo|Chiusura sinistra|Loquet gauche|Linker Verschluss|左ラッチ
Right latch|Cierre derecho|Chiusura destra|Loquet droit|Rechter Verschluss|右ラッチ
Gasket|Junta|Guarnizione|Joint|Dichtung|ガスケット
Fit test kit|Kit de prueba de encaje|Kit prova incastri|Kit d'essai d'ajustement|Passungsprüfsatz|はめ合いテストキット
Files exported.|Archivos exportados.|File esportati.|Fichiers exportés.|Dateien exportiert.|ファイルを書き出しました。
Import request sent to Plater.|Solicitud enviada a la mesa.|Richiesta inviata al piatto.|Demande envoyée au plateau.|Importanfrage an das Druckbett gesendet.|プレートへの読み込みを要求しました。
Animate lid|Animar tapa|Anima coperchio|Animer le couvercle|Deckel animieren|ふたをアニメーション
Auto-Rotate|Rotación automática|Rotazione automatica|Rotation automatique|Automatisch drehen|自動回転
Sync active printer|Sincronizar impresora activa|Sincronizza stampante attiva|Synchroniser l'imprimante active|Aktiven Drucker synchronisieren|使用中のプリンターと同期
Material|Material|Materiale|Matériau|Material|マテリアル
Studio sections|Secciones del estudio|Sezioni dello studio|Sections de l'atelier|Studio-Bereiche|スタジオのセクション
Section cut mode|Modo de corte|Modalità sezione|Mode de coupe|Schnittmodus|断面モード
Snap-fit|Encaje|A scatto|Clipsé|Schnappdeckel|スナップ式
Rugged|Reforzada|Rinforzata|Renforcé|Robust|頑丈
Sliding|Deslizante|Scorrevole|Coulissant|Schiebedeckel|スライド式
Screw|Atornillada|Avvitata|Vissé|Schraubdeckel|ねじ止め式
Off|Sin corte|Nessuno|Aucun|Aus|オフ
"""

TRANSLATIONS: dict[str, dict[str, str]] = {code: {} for code in SUPPORTED_LANGUAGES[2:]}
for _line in _ROWS.strip().splitlines():
    _parts = _line.split("|")
    if len(_parts) != 6:
        raise ValueError("Invalid offline translation row: " + _parts[0])
    for _code, _text in zip(SUPPORTED_LANGUAGES[2:], _parts[1:]):
        TRANSLATIONS[_code][_parts[0]] = _text
del _line, _parts, _code, _text


def translate_text(english: str, language: object, portuguese: str | None = None) -> str:
    code = normalize_language(language)
    if code == "pt":
        return portuguese if portuguese is not None else english
    return TRANSLATIONS.get(code, {}).get(english, english)
