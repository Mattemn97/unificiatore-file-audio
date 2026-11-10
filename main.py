import logging
import shutil
from pathlib import Path
from typing import List, Optional

# Librerie di terze parti
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

# Importazione del logger aziendale
from custom_logger import logger

# Inizializzazione della console Rich per l'interfaccia utente
console = Console()

# Configurazione Percorsi Statici di Sistema
FFMPEG_BINARY_PATH = Path(r"C:\ffmpeg\bin")

class DipendenzaMancanteError(Exception):
    """Sollevata quando FFmpeg non è rintracciabile nel sistema."""
    pass

class AudioLibroProcessor:
    """
    Gestisce l'unificazione di file audio in ordine alfabetico.
    
    Questa classe si occupa della validazione dell'ambiente di esecuzione,
    della scansione dei file e della generazione del file finale unificato.
    """

    ESTENSIONI_SUPPORTATE = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}

    def __init__(self):
        """
        Inizializza il processore e configura le dipendenze esterne.
        """
        logger.debug("Inizializzazione AudioLibroProcessor.")
        self._configura_ambiente_sistema()

    def _configura_ambiente_sistema(self) -> None:
        """
        Configura il percorso di FFmpeg e ne verifica l'accessibilità.
        
        Raises:
            DipendenzaMancanteError: Se i binari di FFmpeg non vengono trovati.
        """
        # Iniezione del percorso FFmpeg fornito nella configurazione di pydub
        if FFMPEG_BINARY_PATH.exists():
            ffmpeg_exe = FFMPEG_BINARY_PATH / "ffmpeg.exe"
            ffprobe_exe = FFMPEG_BINARY_PATH / "ffprobe.exe"
            
            AudioSegment.converter = str(ffmpeg_exe)
            AudioSegment.ffprobe = str(ffprobe_exe)
            logger.debug(f"Percorsi FFmpeg configurati manualmente: {FFMPEG_BINARY_PATH}")
        
        # Verifica finale della disponibilità del comando
        if not shutil.which("ffmpeg") and not Path(AudioSegment.converter).exists():
            logger.critical("FFmpeg non rintracciato nel PATH o nel percorso specificato.")
            raise DipendenzaMancanteError("FFmpeg necessario non trovato. Verificare l'installazione in C:\\ffmpeg\\bin.")

    def recupera_file_sorgente(self, cartella_input: Path) -> List[Path]:
        """
        Scansiona la directory e restituisce i file supportati ordinati alfabeticamente.

        Args:
            cartella_input (Path): Percorso della directory da scansionare.

        Returns:
            List[Path]: Elenco ordinato dei percorsi dei file audio.
        """
        logger.debug(f"Scansione file in corso nella directory: {cartella_input}")
        
        file_validi = [
            f for f in cartella_input.iterdir()
            if f.is_file() and f.suffix.lower() in self.ESTENSIONI_SUPPORTATE
        ]
        
        # Ordinamento alfabetico rigoroso
        file_validi.sort(key=lambda x: x.name.lower())
        
        logger.info(f"Scansione ultimata. Trovati {len(file_validi)} file audio validi.")
        return file_validi

    def unifica_audio(self, lista_file: List[Path]) -> Optional[AudioSegment]:
        """
        Concatena i segmenti audio in un unico flusso.

        Args:
            lista_file (List[Path]): Lista ordinata dei file da processare.

        Returns:
            Optional[AudioSegment]: Oggetto audio unificato o None in caso di fallimento.
        """
        if not lista_file:
            logger.warning("Lista file vuota. Nessuna operazione di unificazione possibile.")
            return None

        risultato_finale = AudioSegment.empty()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Elaborazione segmenti audio...", total=len(lista_file))

            for percorso in lista_file:
                try:
                    logger.debug(f"Caricamento in memoria: {percorso.name}")
                    audio_segmento = AudioSegment.from_file(str(percorso))
                    risultato_finale += audio_segmento
                    progress.update(task, advance=1, description=f"Completato: {percorso.name}")
                except (CouldntDecodeError, Exception) as e:
                    logger.error(f"Errore durante il parsing del file {percorso.name}: {e}", exc_info=True)
                    continue

        return risultato_finale

    def esporta_file_unificato(self, audio: AudioSegment, percorso_output: Path) -> bool:
        """
        Salva il flusso audio unificato su disco.

        Args:
            audio (AudioSegment): Flusso audio da esportare.
            percorso_output (Path): Percorso di destinazione del file finale.

        Returns:
            bool: Esito dell'operazione di scrittura.
        """
        try:
            formato = percorso_output.suffix.replace(".", "").lower() or "mp3"
            logger.info(f"Inizio esportazione file finale: {percorso_output}")
            
            # Creazione ricorsiva delle directory di destinazione
            percorso_output.parent.mkdir(parents=True, exist_ok=True)
            
            audio.export(str(percorso_output), format=formato)
            
            logger.info("Esportazione completata con successo.")
            return True
        except Exception as e:
            logger.error(f"Errore critico durante l'esportazione: {e}", exc_info=True)
            return False

def visualizza_anteprima_operazione(file_audio: List[Path]) -> None:
    """Genera una tabella riepilogativa dei file rilevati per l'utente."""
    tabella = Table(title="Sequenza di Unificazione Rilevata", header_style="bold blue")
    tabella.add_column("Ordine", justify="right", style="cyan")
    tabella.add_column("Nome File", style="white")
    tabella.add_column("Formato", justify="center", style="green")

    for i, file in enumerate(file_audio, 1):
        tabella.add_row(str(i), file.name, file.suffix.upper())

    console.print(tabella)

def main() -> None:
    """Entry point dell'applicazione."""
    console.rule("[bold blue]UNIFICATORE AUDIO ENTERPRISE")
    
    try:
        # 1. Inizializzazione e validazione ambiente
        processore = AudioLibroProcessor()
        
        # 2. Acquisizione input utente
        sorgente_str = Prompt.ask("\nInserire il percorso della cartella contenente i file audio")
        output_str = Prompt.ask("Inserire il percorso completo per il file di output (es. C:\\esito\\finale.mp3)")
        
        path_sorgente = Path(sorgente_str)
        path_output = Path(output_str)

        if not path_sorgente.is_dir():
            logger.warning(f"Percorso sorgente non valido: {sorgente_str}")
            console.print("[bold red]Errore:[/] La cartella sorgente non esiste.")
            return

        # 3. Scansione file
        file_da_unire = processore.recupera_file_sorgente(path_sorgente)

        if not file_da_unire:
            console.print("[yellow]Nessun file audio supportato trovato nella directory selezionata.[/]")
            return

        visualizza_anteprima_operazione(file_da_unire)

        # 4. Processamento audio
        audio_finale = processore.unifica_audio(file_da_unire)

        if audio_finale:
            # 5. Scrittura su disco
            if processore.esporta_file_unificato(audio_finale, path_output):
                console.print(f"\n[bold green]Procedura terminata con successo.[/]")
                console.print(f"File salvato in: [white]{path_output}[/]")
            else:
                console.print("\n[bold red]Errore durante il salvataggio del file.[/]")

    except DipendenzaMancanteError as e:
        console.print(f"\n[bold red]Errore di Sistema:[/] {e}")
    except KeyboardInterrupt:
        logger.info("Interruzione manuale dell'utente (SIGINT).")
        console.print("\n[yellow]Operazione interrotta.[/]")
    except Exception as e:
        logger.critical(f"Errore irreversibile: {e}", exc_info=True)
        console.print("\n[bold red]Si è verificato un errore critico. Consultare i log per i dettagli.[/]")

if __name__ == "__main__":
    main()