import argparse

from app import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Painel de monitoramento da temperatura.")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="usa a simulação de 0 a 100 °C sem conectar ao sensor",
    )
    argumentos = parser.parse_args()
    main(debug=argumentos.debug)
