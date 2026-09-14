from app.models.usuario import Usuario
from app.models.tipo_unidade import TipoUnidade
from app.models.predio import Predio
from app.models.unidade import Unidade, UsuarioUnidade
from app.models.tipo_sala import TipoSala
from app.models.sala import Sala
from app.models.equipamento import (
    TipoEquipamento, CampoTipoEquipamento, Marca, Modelo,
    Equipamento, EquipamentoCampoValor, EquipamentoUsuario
)
from app.models.chamado import Divisao, SetorManutencao, UsuarioSetor, Chamado, ChamadoHistorico, ChamadoFoto, ChamadoSolicitacaoItem, AnexoAndamento, ChamadoAtribuido
from app.models.status_chamado import StatusChamado
from app.models.notificacao import Notificacao
from app.models.contrato import Contrato, ContratoTipoEquipamento, ContratoAcao
from app.models.transferencia import (
    TransferenciaEquipamento,
    DocumentoTransferencia,
    ItemDocumentoTransferencia,
    ItemLojinha,
    HistoricoEquipamento,
)
from app.models.ficha_cnes import FichaCnesVinculo
from app.models.matricula import MatriculaProfissional
from app.models.tipo_link import TipoLink
from app.models.link_util import LinkUtil
from app.models.empresa import EmpresaContratada
from app.models.agenda import AgendaEvento
from app.models.feriado import Feriado
from app.models.cbo import CBO
from app.models.sueq import (
    SueqParlamentar, SueqUnidade, SueqProcesso, SueqEmenda, SueqEmendaItem,
    SueqChamado, SueqChamadoControle,
)
from app.models.nsp import (
    NspCatalogo, NspOcorrencia, NspAnexo, NspAndamento, NspEncaminhamento, NspAcao,
)
from app.models.identidade import IdentidadeSistema, SistemaAsset
from app.models.noticias import (
    TipoAcao, Comunicado, ComunicadoAnexo, ComunicadoCiencia,
    AcaoLocal, AcaoLocalFoto, AcaoLocalCurtida, AcaoLocalComentario,
)
from app.models.perfil_permissao import PerfilPermissao
from app.models.auditoria import Auditoria
from app.models.planejamento import (
    Planejamento, PlanejamentoAnexo, AcaoPlanejamento,
    AcaoObservacao, AcaoObservacaoAnexo,
)
from app.models.falta_abonada import FaltaAbonada
from app.models.contrato_financeiro import ContratoFinanceiro
from app.models.solicitacao_vinculo import SolicitacaoVinculo