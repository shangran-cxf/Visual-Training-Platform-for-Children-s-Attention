// const { createApp, ref, reactive, computed, onMounted } = Vue;

// createApp({
//   setup() {
//     const step = ref(3);
//     const gazeDir = ref('居中');
//     const blinkRate = ref(18);
//     const headPose = ref('0°');
//     const faceDistance = ref(42);

//     const attentionDir = ref(80);
//     const stability = ref(70);
//     const trackAbility = ref(85);
//     const compositeScore = computed(() =>
//       Math.round((attentionDir.value + stability.value + trackAbility.value) / 3)
//     );

//     const ball = reactive({ x: 150, y: 100 });
//     const mouseX = ref(0);
//     const mouseY = ref(0);
//     const mouseInGame = ref(false);
//     const ballArea = ref(null);

//     onMounted(() => {
//       let angle = 0;
//       function ani() {
//         angle += 0.03;
//         if (ballArea.value) {
//           let w = ballArea.value.clientWidth;
//           let h = ballArea.value.clientHeight;
//           ball.x = w / 2 + Math.sin(angle) * 100;
//           ball.y = h / 2 + Math.cos(angle * 1.2) * 60;
//         }
//         requestAnimationFrame(ani);
//       }
//       ani();
//     });

//     function handleMouseMove(e) {
//       const r = e.currentTarget.getBoundingClientRect();
//       mouseX.value = e.clientX - r.left;
//       mouseY.value = e.clientY - r.top;
//       mouseInGame.value = true;
//     }

//     function generateReport() {
//       alert("报告已生成！综合评分：" + compositeScore.value);
//     }

//     return {
//       step, gazeDir, blinkRate, headPose, faceDistance,
//       attentionDir, stability, trackAbility, compositeScore,
//       ball, mouseX, mouseY, mouseInGame, ballArea,
//       handleMouseMove, generateReport
//     }
//   }
// }).mount('#app');
// 打开登录弹窗
function openLogin() {
  document.getElementById("loginModal").style.display = "flex";
}

// 关闭登录弹窗
function closeLogin() {
  document.getElementById("loginModal").style.display = "none";
}

// 登录判断
function login() {
  let user = document.getElementById("username").value;
  let pwd = document.getElementById("password").value;

  //判断用户名和密码
  if (user === "admin" && pwd === "123456") {
    alert("登录成功！");
    location.href = "main.html";
  } else {
    alert("账号或密码错误！");
  }
}

// 退出登录弹窗
function logout() {
  document.getElementById("logoutModal").style.display = "flex";
}

function closeLogout() {
  document.getElementById("logoutModal").style.display = "none";
}

function confirmLogout() {
  alert("已退出登录");
  location.href = "index.html";
}