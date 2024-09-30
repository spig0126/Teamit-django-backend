# 게더어스 - 프로젝트 공모전 팀 매칭 플랫폼
`2023 예비창업패키지 선정` `2024 창업유망팀300 선정`

## 서비스 설명
- 팀 프로젝트를 하고 싶은 많은 대학생들과 취준생들을 위해 개발한 플랫폼으로, 사용자는 이미 존재하는 팀에 지원하거나 새로운 팀을 만들어 팀원을 모집할 수 있습니다.
- 팀 지원 및 팀원 모집에 대해 어려움을 겪지 않도록, 사용자에게 맞는 팀/팀원 추천, 팀/팀원 프로필 공개, 개인 문의 채팅 등 다양한 기능을 제공하고 있습니다. 


## 기술 스택
<img alt="Static Badge" src="https://img.shields.io/badge/Django-092E20.svg?style=flat-square&logo=Django"> <img alt="Static Badge" src="https://img.shields.io/badge/Celery-37814A.svg?style=flat-square&logo=Celery">
<img alt="Static Badge" src="https://img.shields.io/badge/Redis-FF4438.svg?style=flat-square&logo=Redis&logoColor=white">
<img alt="Static Badge" src="https://img.shields.io/badge/Firebase-DD2C00.svg?style=flat-square&logo=Firebase&logoColor=white">
<img alt="Static Badge" src="https://img.shields.io/badge/amazonrds-527FFF.svg?style=flat-square&logo=Amazon%20RDS&logoColor=white">
<img alt="Static Badge" src="https://img.shields.io/badge/amazonec2-FF9900.svg?style=flat-square&logo=Amazon%20EC2&logoColor=white">
<img alt="Static Badge" src="https://img.shields.io/badge/amazons3-569A31.svg?style=flat-square&logo=Amazon%20S3&logoColor=white">
<img alt="Static Badge" src="https://img.shields.io/badge/AWS%20ELB-8C4FFF.svg?style=flat-square&logo=Amazon%20ELB&logoColor=white">
<img alt="Static Badge" src="https://img.shields.io/badge/Github%20Actions-2088FF.svg?style=flat-square&logo=Github%20Actions&logoColor=white">

## 담당 업무
- 관계 데이터베이스 설계
- 클라우드 인프라 구축 및 운영
- 배포 CI/CD 구축
- RESTful API 개발 
- Django Signal을 이용한 배지 푸시알림 구현
- 웹소켓 기반 실시간 채팅 기능 및 푸시알림 구현
- 기능 기획 및 정리
- 동기 및 비동기 테스팅

## 구현 기능에 따른 앱 맛보기
<table style="width: 100%; table-layout: auto;">
  <tr>
    <th>기능</th>
    <th>영상</th>
    <th>기능</th>
    <th>영상</th>
  </tr>
  <tr>
    <td>
      <strong>&lt; 사용자 프로필 공유 &gt;</strong><br/>
      <p style="color: grey">관심 직무 및 활동, 활동 지역, 사용 가능한 툴, 경험, 프로필 링크 등</p>
    </td>
    <td style="text-align: center;">
      <img src="https://github.com/user-attachments/assets/3f100314-2442-4dde-b76b-80ab7e86b64e" style="max-width: 100%;" />
    </td>
    <td>
      <strong>&lt; 팀 프로필 공유 &gt;</strong><br/>
      <p style="color: grey">프로젝트 주제, 팀 소개, 모집 직무, 활동 기간 등</p>
    </td>
    <td style="text-align: center;">
      <img src="https://github.com/user-attachments/assets/05ce88fe-9945-444b-b00f-3827c2a6bc81" style="max-width: 100%;" />
    </td>
  </tr>
  <tr>
    <td>
      <strong>&lt; 사용자에 대한 후기 기능 &gt;</strong><br/>
      <p style="color: grey">사용자와 함께 했던 팀원이 남길 수 있는 기능으로, 평점과 키워드, 그리고 후기 글을 남길 수 있습니다</p>
    </td>
    <td style="text-align: center;">
      <img src="https://github.com/user-attachments/assets/c2ae2335-0f2b-469e-aae6-a8e76b8ee63c" style="max-width: 100%;" />
    </td>
    <td>
      <strong>&lt; 사용자 프로필 기반으로 팀원/팀 추천 &gt;</strong><br/>
      <p style="color: grey">사용자가 선호하는 직무, 분야 등을 바탕으로 팀/팀원 추천</p>
    </td>
    <td style="text-align: center;">
      <img src="https://github.com/user-attachments/assets/640ef59b-a857-4cd5-849d-ca16203c4fc4" style="max-width: 100%;" />
    </td>
  </tr>
  <tr>
    <td>
      <strong>&lt; 개인 / 팀 / 팀 문의 채팅 &gt;</strong>
      <ul>
        <li>개인 채팅: 사용자가 직접 다른 사람에게 리쿠르팅 제의나 문의할 수 있는 채팅방</li>
        <li>팀 채팅: 사용자가 자기 팀원끼리 소통할 수 있는 단체 채팅방</li>
        <li>팀 문의 채팅: 사용자가 관심있는 팀에게 문의할 수 있는 채팅방</li>
      </ul>
    </td>
    <td style="text-align: center;">
      <img src="https://github.com/user-attachments/assets/a9c83a14-e961-45d6-831f-f933753dcf64" style="max-width: 100%;" />
    </td>
    <td>
      <strong>&lt; 사용자/팀 검색 기능 &gt;</strong><br/>
      <p style="color: grey">키워드, 분야, 이름, 직무 등으로 검색 가능합니다</p>
    </td>
    <td style="text-align: center;">
      <img src="https://github.com/user-attachments/assets/4a5d0c63-3893-45f7-a240-e0d3f4d9537f" style="max-width: 100%;" />
    </td>
  </tr>
  <tr>
    <td>
      <strong>&lt; 배지 기능 &gt;</strong><br/>
      <p style="color: grey">앱 사용 활성화를 위해 다양한 앱 내 활동에 따른 배지 획득 기능 (푸시알림으로 획득한 배지 알려줌)</p>
    </td>
    <td style="text-align: center;">
      <img src="https://github.com/user-attachments/assets/a459ec46-21af-4251-94c4-d87fb2152b26" style="max-width: 100%;" />
    </td>
    <td></td>
    <td></td>
  </tr>
</table>
