const socket = io();


const config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    parent: 'gameContainer',
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { y: 0 },
            debug: false
        }
    },
    scene: {
        preload: preload,
        create: create,
        update: update
    }
};


let player;
let players = {}; // Object to store all players
let bullets; // Group for bullets
let enemies; // Group for enemies
let healthText;
let gameOver = false;
let spawnCounter = 0; // Counter for deterministic spawn positions
let playerScore = 0; // Score for the main player
let opponentScore = 0; // Display opponent's score
let scoreText;
let opponentScoreText;
let opponentHealth = 100; // Display opponent's health
let opponentHealthText;


function preload() {
    this.load.image('player', 'static/assets/player.png');
    this.load.image('background', 'static/assets/background.png');
    this.load.image('bullet', 'static/assets/bullet.png');
    this.load.image('enemy', 'static/assets/enemy.png');
}


function create() {
    background = this.add.sprite(0, 0, 'background')
        .setOrigin(0, 0)
        .setDisplaySize(config.width, config.height);


    player = this.add.sprite(400, 300, 'player');
    player.setDisplaySize(48, 64);
    this.physics.add.existing(player);
    player.body.setCollideWorldBounds(true);
    player.health = 100;


    bullets = this.physics.add.group();
    enemies = this.physics.add.group();


    socket.on('connect', () => {
        players[socket.id] = player;
        socket.emit('newPlayer', { x: player.x, y: player.y });
        socket.emit('scoreUpdate', { id: socket.id, score: playerScore });
    });


    healthText = this.add.text(16, 16, 'Health: 100', { fontSize: '32px', fill: '#fff' });
    scoreText = this.add.text(16, 60, 'Score: 0', { fontSize: '32px', fill: '#fff' });
   
    opponentScoreText = this.add.text(config.width - 500, 16, 'Opponent Score: 0', { fontSize: '32px', fill: '#fff' });
    opponentHealthText = this.add.text(config.width - 500, 60, 'Opponent Health: 100', { fontSize: '32px', fill: '#fff' });


    socket.on('update_player_positions', (updatedPlayers) => {
        for (const id in updatedPlayers) {
            if (id === socket.id) continue;


            if (!players[id]) {
                const newPlayer = this.add.sprite(updatedPlayers[id].x, updatedPlayers[id].y, 'player');
                newPlayer.setDisplaySize(48, 64);
                players[id] = newPlayer;
            } else {
                players[id].x = updatedPlayers[id].x;
                players[id].y = updatedPlayers[id].y;
            }
        }
    });


    socket.on('removePlayer', (id) => {
        if (players[id]) {
            players[id].destroy();
            delete players[id];
        }
    });


    socket.on('bulletFired', (data) => {
        fireBullet.call(this, data.x, data.y, data.angle);
    });


    this.time.addEvent({
        delay: 200,
        callback: shootBullet,
        callbackScope: this,
        loop: true
    });


    this.time.addEvent({
        delay: 1000,
        callback: spawnEnemy,
        callbackScope: this,
        loop: true
    });


    socket.on('enemy_spawned', (data) => {
        spawnEnemyAtPosition.call(this, data.x, data.y);
    });


    this.physics.add.overlap(bullets, enemies, damageEnemy, null, this);


    // Check for collision between the player and enemies
    this.physics.add.overlap(player, enemies, enemyTouchesPlayer, null, this);




    socket.on('opponent_health', (data) => {
        if (data.id !== socket.id) {
            opponentHealth = data.health;
            opponentHealthText.setText('Opponent Health: ' + opponentHealth);
        }
    });
}


// Deterministic function for calculating spawn points
function calculateSpawnPoint(counter) {
    const xOptions = [0, config.width, Math.floor(config.width / 2)];
    const yOptions = [0, config.height, Math.floor(config.height / 2)];


    const x = xOptions[counter % xOptions.length];
    const y = yOptions[(Math.floor(counter / xOptions.length)) % yOptions.length];


    return { x, y };
}


// Function to spawn an enemy with a synchronized "random" position
function spawnEnemy() {
    if (gameOver) return;


    // Calculate a deterministic spawn position based on the spawnCounter
    const { x, y } = calculateSpawnPoint(spawnCounter);
    spawnCounter++; // Increment the counter for the next spawn


    // Broadcast spawn position to all players
    socket.emit('spawn_enemy', { x, y });
    spawnEnemyAtPosition.call(this, x, y);
}


// Function to spawn an enemy at a specific position with health
function spawnEnemyAtPosition(x, y) {
    const enemy = this.add.sprite(x, y, 'enemy');
    enemy.setDisplaySize(48, 60);
    this.physics.add.existing(enemy);
    enemy.health = 30; // Set health for the enemy
    enemies.add(enemy);
}


// Function to shoot a bullet
function shootBullet() {
    if (gameOver) return;
    const pointer = this.input.mousePointer;
    const angle = Phaser.Math.Angle.Between(player.x, player.y, pointer.x, pointer.y);


    // Emit and fire the bullet
    socket.emit('shootBullet', { x: player.x, y: player.y, angle: angle });
    fireBullet.call(this, player.x, player.y, angle);
}


// Function to fire a bullet
function fireBullet(x, y, angle) {
    const bulletSpeed = 500;
    const bullet = bullets.create(x, y, 'bullet');
    bullet.setDisplaySize(16, 16);
    bullet.setAngle((angle * 180) / Math.PI); // Convert radian to degree
    bullet.body.velocity.x = Math.cos(angle) * bulletSpeed;
    bullet.body.velocity.y = Math.sin(angle) * bulletSpeed;


    // Destroy bullet after 2 seconds
    this.time.delayedCall(2000, () => {
        if (bullet) bullet.destroy();
    });
}


// Function to find the nearest player to an enemy
function findNearestPlayer(enemy) {
    let nearestPlayer = player;
    let shortestDistance = Phaser.Math.Distance.Between(player.x, player.y, enemy.x, enemy.y);


    for (const id in players) {
        const otherPlayer = players[id];
        const distance = Phaser.Math.Distance.Between(otherPlayer.x, otherPlayer.y, enemy.x, enemy.y);
        if (distance < shortestDistance) {
            shortestDistance = distance;
            nearestPlayer = otherPlayer;
        }
    }


    return nearestPlayer;
}


// Function to reduce enemy health and destroy it if health is zero
function damageEnemy(bullet, enemy) {
    bullet.destroy();
    enemy.health -= 10;


    if (enemy.health <= 0) {
        enemy.destroy();
        playerScore += 1; // Increment local player's score
        scoreText.setText('Score: ' + playerScore);


        // Emit score update to the server
        socket.emit('scoreUpdate', { id: socket.id, score: playerScore});
    }
}


// Function to handle player taking damage when touched by an enemy
function enemyTouchesPlayer(player, enemy) {
    player.health -= 10; // Reduce player health by 10
    healthText.setText('Health: ' + player.health); // Update the health text


    // Emit the updated health to the server
    socket.emit('healthUpdate', { id: socket.id, health: player.health });


    if (player.health <= 0) {
        gameOver = true;
        healthText.setText('Health: 0');
        console.log('Game Over');
        // Optionally, you could add code here to show a game-over message or restart the game
    }


    // Optionally destroy the enemy or apply further effects
    enemy.destroy();
}


function update() {
    if (gameOver) return;


    const cursors = this.input.keyboard.createCursorKeys();
    this.wKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.W);
    this.aKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.A);
    this.sKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.S);
    this.dKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.D);
    const speed = 200;


    let moved = false;


    if (cursors.left.isDown || this.aKey.isDown) {
        player.body.setVelocityX(-speed);
        moved = true;
    } else if (cursors.right.isDown || this.dKey.isDown) {
        player.body.setVelocityX(speed);
        moved = true;
    } else {
        player.body.setVelocityX(0);
    }


    if (cursors.up.isDown || this.wKey.isDown) {
        player.body.setVelocityY(-speed);
        moved = true;
    } else if (cursors.down.isDown || this.sKey.isDown) {
        player.body.setVelocityY(speed);
        moved = true;
    } else {
        player.body.setVelocityY(0);
    }


    if (moved) {
        socket.emit('playerMove', { x: player.x, y: player.y });
        console.log(`Player moved to position: x=${player.x}, y=${player.y}`);
    }


    // Make each enemy move toward the nearest player
    enemies.getChildren().forEach(enemy => {
        const target = findNearestPlayer(enemy);
        this.physics.moveToObject(enemy, target, 100);
    });
}


new Phaser.Game(config);



