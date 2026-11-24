# webhook-replay-check

Independent demo, not affiliated with SGI.

Uma ferramenta pequena que testa se um handler de webhook aguenta entrega repetida e fora de ordem. Provedores de webhook costumam entregar "pelo menos uma vez": o mesmo evento pode chegar duas vezes, ou o evento 2 pode chegar antes do 1. A ferramenta reproduz isso com eventos de exemplo e compara o estado final com o de uma entrega limpa.

Todos os dados são de exemplo, inventados. Nada de rede, login ou dado real.

## Como rodar

Precisa de Python 3.10 ou mais novo. Sem dependências para rodar; só `pytest` para os testes.

```bash
python -m webhook_replay_check                  # compara dois handlers de exemplo
python -m webhook_replay_check --runs 500 --seed 3
python -m webhook_replay_check --handler meu_modulo:MeuHandler   # seu handler
pip install pytest && python -m pytest -q       # testes
```

Seu handler precisa de dois métodos: `apply(event)` e `snapshot()` (um dict com o estado). Com `--handler`, o comando sai com código 1 se algum cenário terminar em estado diferente.

## O que acontece com os exemplos

Saída real de `python -m webhook_replay_check`:

```
FAIL  NaiveHandler: 196/200 noisy runs ended in a different state
  expected: {"status": {"ord_A": "paid", "ord_B": "refunded", "ord_C": "pending"}, "revenue": 10000}
  got:      {"status": {"ord_A": "pending", "ord_B": "refunded", "ord_C": "pending"}, "revenue": 1000}
PASS  IdempotentHandler: 0/200 noisy runs ended in a different state
```

O `NaiveHandler` aceita toda entrega. Um evento `payment.paid` repetido soma a receita duas vezes, e um `payment.created` atrasado volta o pedido para "pending". O `IdempotentHandler` descarta ids já vistos e guarda eventos que chegaram cedo até a vez deles.

## What was tested

- 9 testes offline com pytest, rodando no GitHub Actions a cada push.
- Estado esperado dos dados de exemplo em entrega limpa.
- Duplicata simples soma receita dobrada no handler ingênuo e uma vez no idempotente.
- Troca de ordem de dois eventos deixa o status errado no handler ingênuo.
- A mesma seed gera o mesmo cenário.
- Código de saída da linha de comando.

## What was not tested

- Nenhum provedor de webhook real. Os eventos (`payment.created`, `payment.paid`, `payment.refunded`) são inventados.
- Só duplicata e troca de ordem. Não simula perda de evento, atraso longo, concorrência entre processos nem falha no meio de um evento.
- O `IdempotentHandler` guarda tudo em memória. Em produção o controle de ids vistos precisa de banco ou fila, com transação.
- Assume número de sequência por pedido. Nem todo provedor manda isso.
- Não é uma prova: 200 execuções aleatórias achar zero falhas não garante que não existe uma.

## Licença

MIT
