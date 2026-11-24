# Roteiro de apresentação

Disciplina: Computação Gráfica
Projeto: Monitor de temperatura em Pygame
Integrantes: Guilherme Cezarino, Gabriel Eduardo e Felipe Guedes

## Slide 1: Monitor de temperatura em Pygame

Nosso trabalho é um painel 2D feito em Python com Pygame que transforma leituras de temperatura em elementos visuais em tempo real. Ele funciona em dois modos: conectado a um sensor pela rede, na faixa de 0 a 50 graus, ou em simulação local pelo argumento `--debug`, indo de 0 a 100 graus.

## Slide 2: Loop principal e controle de quadros (`app.py`)

Toda a atualização da tela passa pelo loop principal em `app.py`. Travamos a execução em 60 quadros por segundo e calculamos o `dt`, que é o tempo entre um quadro e outro, limitado a 0,1 segundo. Isso garante que as animações andem na mesma velocidade em computadores diferentes.

Na hora de desenhar, seguimos uma ordem fixa de camadas: primeiro o gradiente de fundo, depois as partículas e por último o termômetro, os textos, o cubo de gelo e o gráfico. No fim do ciclo, `pygame.display.flip()` troca o buffer e mostra o quadro inteiro de uma só vez, evitando que a imagem pisque.

## Slide 3: Interpolação linear RGB e gradiente com cache (`visuals.py`)

Para relacionar a temperatura com a cor, a função `cor_da_temperatura` normaliza o valor atual e faz uma interpolação linear nos canais R, G e B entre pontos de referência que vão do azul ao vermelho.

No fundo da janela, o gradiente mistura duas paletas verticais, uma fria e uma quente. Como calcular 600 pixels de altura em todo quadro pesaria sem necessidade, geramos uma coluna de 1 pixel de largura, esticamos para os 900 pixels da tela e guardamos o resultado em um cache com 201 níveis.

## Slide 4: Derretimento do gelo por alpha blending (`visuals.py`)

O cubo de gelo vem de um spritesheet chamado `ice_cube_states.png`, que tem apenas quatro imagens desenhadas. Para a transição entre um estado e outro ficar contínua, a função `quadro_interpolado_gelo` gera até 120 passos intermediários entre dois quadros vizinhos.

Nesse cálculo, multiplicamos os canais RGB e o canal alfa de cada imagem pelo seu peso e somamos as duas camadas. Assim, até as bordas transparentes se misturam sem cortes. Além disso, usamos `math.sin` com o tempo decorrido para o cubo oscilar na vertical e para o anel ao redor pulsar.

## Slide 5: Coordenadas de tela no termômetro e no gráfico (`visuals.py`)

O termômetro e o gráfico histórico são desenhados diretamente com primitivas 2D do Pygame: retângulos com cantos arredondados, círculos, linhas e polilinhas.

Um detalhe importante de Computação Gráfica aqui é o sistema de coordenadas. Na tela, o eixo Y começa em zero no topo e cresce para baixo. Por isso, para o líquido do termômetro subir quando a temperatura aumenta, calculamos a altura proporcional e subtraímos da coordenada da base. No gráfico histórico acontece a mesma coisa, com a escala vertical se ajustando às últimas 120 leituras.

## Slide 6: Física térmica, paralaxe e camada translúcida (`effects.py`)

O arquivo `effects.py` cuida do sistema de partículas em toda a área de 900 por 600 pixels. Conforme a faixa de temperatura, a classe `SistemaParticulas` cria neve e bolhas no frio, gotas e vapor na faixa intermediária e brasas no calor.

Cada partícula tem um fator de profundidade entre 0,45 e 1,0, que altera velocidade, tamanho e opacidade para dar noção de paralaxe. Todas elas são desenhadas juntas em uma única superfície `SRCALPHA`, com entrada e saída graduais.

## Slide 7: Resposta ao cursor e colisões com a interface (`effects.py`)

As partículas também reagem ao usuário e aos objetos da tela. Quando o cursor passa a menos de 130 pixels de uma partícula, aplicamos uma força radial de repulsão somada a um componente tangencial, o que cria um leve giro ao redor do ponteiro. Ao clicar com o botão esquerdo, sai uma rajada radial com o tipo de partícula do clima atual.

Nos elementos da interface, as partículas contornam o anel do cubo de gelo e o corpo do termômetro, e as gotas ou flocos quicam ao atingir o topo do gráfico.

## Slide 8: Demonstração em tempo real (`termometer.py --debug`)

Aqui executamos `python termometer.py --debug` para mostrar o comportamento completo na prática.

(Abrir a janela de simulação e percorrer os três momentos: entre 0 e 15 graus com o fundo azul, cubo sólido e neve caindo; entre 20 e 35 graus com o gelo derretendo e gotas quicando no gráfico; acima de 40 graus com o fundo quente, vapor e brasas subindo. Por fim, passar o mouse e clicar na tela para mostrar a dispersão e a rajada.)
