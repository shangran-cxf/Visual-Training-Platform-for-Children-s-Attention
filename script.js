
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
