'use strict'

// O pathfinder e JavaScript nativo. Manter esta camada pequena evita criar
// classes JS (Movements/GoalBlock) atraves da ponte Python-JavaScript, que e
// justamente onde chamadas com `new` variam entre versoes do JSPyBridge.
const { pathfinder, Movements, goals } = require('mineflayer-pathfinder')

const estados = new WeakMap()

function estadoDo (bot) {
  if (!estados.has(bot)) {
    estados.set(bot, {
      instalado: false,
      status: 'inativo',
      chegou: false,
      reset: null
    })
  }
  return estados.get(bot)
}

function instalar (bot) {
  const estado = estadoDo(bot)
  if (estado.instalado) return

  bot.loadPlugin(pathfinder)
  estado.instalado = true

  bot.on('path_update', resultado => {
    estado.status = resultado.status || 'atualizado'
  })
  bot.on('goal_reached', () => {
    estado.chegou = true
    estado.status = 'meta'
  })
  bot.on('path_reset', motivo => {
    estado.reset = String(motivo)
  })
}

function configurar (bot, modoDidatico = false) {
  const movimentos = new Movements(bot)
  movimentos.canDig = false
  movimentos.allow1by1towers = false
  movimentos.scafoldingBlocks = []
  movimentos.allowParkour = true
  // No modo didatico o alcance cai para o salto andando (dois blocos),
  // suficiente para frente_1 e bem mais facil de enxergar na apresentacao.
  movimentos.allowSprinting = !modoDidatico
  movimentos.allowFreeMotion = false
  movimentos.allowEntityDetection = false
  movimentos.maxDropDown = 0

  bot.pathfinder.setMovements(movimentos)
  bot.pathfinder.thinkTimeout = 10000
  bot.pathfinder.tickTimeout = 40
}

function iniciar (bot, x, y, z) {
  const estado = estadoDo(bot)
  estado.status = 'calculando'
  estado.chegou = false
  estado.reset = null
  bot.pathfinder.setGoal(new goals.GoalBlock(
    Math.floor(x), Math.floor(y), Math.floor(z)
  ))
}

function parar (bot) {
  if (bot.pathfinder) bot.pathfinder.setGoal(null)
}

function consultar (bot) {
  const estado = estadoDo(bot)
  return JSON.stringify({
    status: estado.status,
    chegou: estado.chegou,
    reset: estado.reset,
    movendo: Boolean(bot.pathfinder && bot.pathfinder.isMoving())
  })
}

module.exports = { instalar, configurar, iniciar, parar, consultar }
